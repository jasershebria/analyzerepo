import * as child_process from 'child_process';
import type Anthropic from '@anthropic-ai/sdk';
import { BaseTool } from './base/base-tool';

// Ported from claude-code/src/tools/BashTool/bashSecurity.ts
const DESTRUCTIVE_PATTERNS = [
  /rm\s+-rf\s+[/~]/,
  /mkfs/,
  /dd\s+if=\/dev\/(zero|random|urandom)/,
  /:\(\)\s*\{\s*:\|:&\s*\};:/,   // fork bomb
  />\s*\/dev\/sda/,
];

const COMMAND_SUBSTITUTION_PATTERNS = [/\$\(/, /`[^`]+`/, /<\(/, />\(/];

const ZSH_DANGEROUS = new Set(['zmodload', 'zpty', 'ztcp', 'zsocket']);

function checkSecurity(command: string): void {
  for (const pat of DESTRUCTIVE_PATTERNS) {
    if (pat.test(command)) throw new Error(`Command blocked (destructive pattern): ${command}`);
  }
  for (const pat of COMMAND_SUBSTITUTION_PATTERNS) {
    if (pat.test(command) && /rm|mkfs|dd|fork/.test(command)) {
      throw new Error(`Command blocked (dangerous substitution): ${command}`);
    }
  }
  const firstWord = command.trim().split(/\s+/)[0];
  if (ZSH_DANGEROUS.has(firstWord)) throw new Error(`Command blocked (zsh dangerous): ${command}`);
}

export class BashTool extends BaseTool {
  readonly name = 'bash';
  readonly description =
    'Execute a shell command. Returns stdout and stderr. ' +
    'Timeout default is 120s, max 600s. Destructive commands (rm -rf /, mkfs, fork bombs) are blocked.';
  readonly isConcurrencySafe = false;

  definition(): Anthropic.Tool {
    return {
      name: this.name,
      description: this.description,
      input_schema: {
        type: 'object' as const,
        properties: {
          command: { type: 'string', description: 'Shell command to execute' },
          timeout: { type: 'number', description: 'Timeout in seconds (default 120, max 600)' },
          run_in_background: { type: 'boolean', description: 'Run in background and return immediately' },
        },
        required: ['command'],
      },
    };
  }

  async execute(args: Record<string, unknown>): Promise<string> {
    const command = String(args.command);
    const timeout = Math.min(Number(args.timeout ?? 120), 600) * 1000;
    const background = Boolean(args.run_in_background ?? false);

    checkSecurity(command);

    if (background) {
      const proc = child_process.spawn('bash', ['-c', command], {
        detached: true,
        stdio: 'ignore',
        cwd: this.workingDir,
      });
      proc.unref();
      return `Process started in background (PID: ${proc.pid})`;
    }

    return new Promise((resolve, reject) => {
      child_process.exec(
        command,
        { cwd: this.workingDir, timeout, maxBuffer: 10 * 1024 * 1024 },
        (err, stdout, stderr) => {
          const out = [stdout?.trim(), stderr?.trim()].filter(Boolean).join('\n');
          if (err && err.killed) return reject(new Error(`Command timed out after ${timeout / 1000}s`));
          resolve(out || '(no output)');
        },
      );
    });
  }
}
