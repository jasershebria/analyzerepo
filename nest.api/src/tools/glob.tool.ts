import * as path from 'path';
import * as fs from 'fs';
import type Anthropic from '@anthropic-ai/sdk';
import { BaseTool } from './base/base-tool';

// Ported from claude-code GlobTool — same 100-file truncation limit
const MAX_FILES = 100;

export class GlobTool extends BaseTool {
  readonly name = 'glob';
  readonly description =
    'Find files matching a glob pattern. Returns matching file paths sorted by modification time. ' +
    'Supports patterns like "**/*.ts", "src/**/*.py". Results truncated at 100 files.';
  readonly isConcurrencySafe = true;

  definition(): Anthropic.Tool {
    return {
      name: this.name,
      description: this.description,
      input_schema: {
        type: 'object' as const,
        properties: {
          pattern: { type: 'string', description: 'Glob pattern to match, e.g. "**/*.ts"' },
          path: { type: 'string', description: 'Root directory to search in (defaults to working dir)' },
        },
        required: ['pattern'],
      },
    };
  }

  async execute(args: Record<string, unknown>): Promise<string> {
    const pattern = String(args.pattern);
    const root = args.path
      ? String(args.path)
      : (this.workingDir ?? process.cwd());

    const fg = await import('fast-glob');
    const files: string[] = await fg.default(pattern, {
      cwd: root,
      onlyFiles: false,
      dot: true,
      ignore: ['node_modules/**', '.git/**'],
    });

    // Sort by mtime descending
    const withMtime = files
      .map((f) => {
        try {
          const stat = fs.statSync(path.join(root, f));
          return { f, mtime: stat.mtimeMs };
        } catch {
          return { f, mtime: 0 };
        }
      })
      .sort((a, b) => b.mtime - a.mtime);

    const truncated = withMtime.length > MAX_FILES;
    const result = withMtime.slice(0, MAX_FILES).map((x) => x.f);

    const output = result.join('\n');
    return truncated ? `${output}\n\n(Showing first ${MAX_FILES} of ${withMtime.length} matches)` : output;
  }
}
