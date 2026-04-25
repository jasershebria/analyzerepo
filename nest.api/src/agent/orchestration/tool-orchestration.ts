// Ported from claude-code/src/services/tools/toolOrchestration.ts
// partitionToolCalls → runTools with concurrent-safe batch vs serial exclusive

import type Anthropic from '@anthropic-ai/sdk';
import type { BaseTool } from '../../tools/base/base-tool';
import type { ToolUpdate } from '../engine/types';

const MAX_CONCURRENCY = 10;

interface ToolBatch {
  isConcurrencySafe: boolean;
  blocks: Anthropic.ToolUseBlock[];
}

export function partitionToolCalls(blocks: Anthropic.ToolUseBlock[], tools: BaseTool[]): ToolBatch[] {
  const registry = Object.fromEntries(tools.map((t) => [t.name, t]));
  const batches: ToolBatch[] = [];
  let current: ToolBatch | null = null;

  for (const block of blocks) {
    const safe = registry[block.name]?.isConcurrencySafe ?? false;
    if (!current || current.isConcurrencySafe !== safe) {
      current = { isConcurrencySafe: safe, blocks: [] };
      batches.push(current);
    }
    current.blocks.push(block);
  }
  return batches;
}

export async function* runTools(
  blocks: Anthropic.ToolUseBlock[],
  tools: BaseTool[],
): AsyncGenerator<ToolUpdate> {
  const registry = Object.fromEntries(tools.map((t) => [t.name, t]));

  for (const batch of partitionToolCalls(blocks, tools)) {
    if (batch.isConcurrencySafe) {
      yield* runBatchConcurrently(batch.blocks, registry);
    } else {
      for (const block of batch.blocks) {
        yield* runSingleTool(block, registry);
      }
    }
  }
}

async function* runBatchConcurrently(
  blocks: Anthropic.ToolUseBlock[],
  registry: Record<string, BaseTool>,
): AsyncGenerator<ToolUpdate> {
  // Run up to MAX_CONCURRENCY in parallel, yield results in order
  const chunks: Anthropic.ToolUseBlock[][] = [];
  for (let i = 0; i < blocks.length; i += MAX_CONCURRENCY) {
    chunks.push(blocks.slice(i, i + MAX_CONCURRENCY));
  }

  for (const chunk of chunks) {
    const results = await Promise.all(chunk.map((b) => collectToolResult(b, registry)));
    for (const updates of results) {
      for (const u of updates) yield u;
    }
  }
}

async function collectToolResult(
  block: Anthropic.ToolUseBlock,
  registry: Record<string, BaseTool>,
): Promise<ToolUpdate[]> {
  const updates: ToolUpdate[] = [];
  for await (const u of runSingleTool(block, registry)) {
    updates.push(u);
  }
  return updates;
}

async function* runSingleTool(
  block: Anthropic.ToolUseBlock,
  registry: Record<string, BaseTool>,
): AsyncGenerator<ToolUpdate> {
  const tool = registry[block.name];

  yield { event: { type: 'tool_start', tool: block.name, input: block.input } };

  if (block.name === 'todo_write') {
    const tasks = (block.input as any)?.todos ?? [];
    yield { event: { type: 'plan', tasks } };
  }

  let output: string;
  let isError = false;

  if (!tool) {
    output = `Unknown tool '${block.name}'. Available: ${Object.keys(registry).join(', ')}`;
    isError = true;
  } else {
    try {
      output = await tool.call(block.input as Record<string, unknown>);
    } catch (e) {
      output = `Error running ${block.name}: ${(e as Error).message}`;
      isError = true;
    }
  }

  yield { event: { type: 'tool_end', tool: block.name, output } };
  yield {
    toolResult: {
      type: 'tool_result',
      tool_use_id: block.id,
      content: output,
      is_error: isError,
    },
  };
}
