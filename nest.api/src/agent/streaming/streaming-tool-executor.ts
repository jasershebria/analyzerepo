// Ported from claude-code/src/services/tools/StreamingToolExecutor.ts
// Executes tools as tool_use blocks stream in; maintains order; runs safe tools concurrently

import type Anthropic from '@anthropic-ai/sdk';
import type { BaseTool } from '../../tools/base/base-tool';

type ToolStatus = 'queued' | 'executing' | 'completed';

interface TrackedTool {
  id: string;
  block: Anthropic.ToolUseBlock;
  isConcurrencySafe: boolean;
  status: ToolStatus;
  result?: { output: string; isError: boolean };
}

export class StreamingToolExecutor {
  private tracked: TrackedTool[] = [];
  private registry: Record<string, BaseTool>;
  private siblingAbort = new AbortController();

  constructor(tools: BaseTool[]) {
    this.registry = Object.fromEntries(tools.map((t) => [t.name, t]));
  }

  addTool(block: Anthropic.ToolUseBlock): void {
    const tool = this.registry[block.name];
    const entry: TrackedTool = {
      id: block.id,
      block,
      isConcurrencySafe: tool?.isConcurrencySafe ?? false,
      status: 'queued',
    };
    this.tracked.push(entry);
    void this.processQueue();
  }

  private canExecute(isSafe: boolean): boolean {
    const executing = this.tracked.filter((t) => t.status === 'executing');
    if (executing.length === 0) return true;
    return isSafe && executing.every((t) => t.isConcurrencySafe);
  }

  private async processQueue(): Promise<void> {
    for (const t of this.tracked) {
      if (t.status !== 'queued') continue;
      if (!this.canExecute(t.isConcurrencySafe)) {
        if (!t.isConcurrencySafe) break;
        continue;
      }

      t.status = 'executing';
      const tool = this.registry[t.block.name];

      try {
        if (this.siblingAbort.signal.aborted) {
          t.result = { output: 'Aborted: a sibling tool errored.', isError: true };
        } else {
          const output = tool
            ? await tool.call(t.block.input as Record<string, unknown>)
            : `Unknown tool '${t.block.name}'`;
          t.result = { output, isError: false };
        }
      } catch (e) {
        t.result = { output: `Error: ${(e as Error).message}`, isError: true };
        if (t.block.name === 'bash') {
          this.siblingAbort.abort('bash_error');
        }
      }

      t.status = 'completed';
      void this.processQueue();
    }
  }

  async drainAll(): Promise<Array<{ block: Anthropic.ToolUseBlock; result: { output: string; isError: boolean } }>> {
    // Wait for all queued/executing tools to complete
    await new Promise<void>((resolve) => {
      const check = () => {
        const done = this.tracked.every((t) => t.status === 'completed');
        if (done) resolve();
        else setTimeout(check, 10);
      };
      check();
    });

    return this.tracked.map((t) => ({
      block: t.block,
      result: t.result ?? { output: 'No result', isError: true },
    }));
  }
}
