import * as child_process from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import type Anthropic from '@anthropic-ai/sdk';
import { BaseTool } from './base/base-tool';

export class GrepTool extends BaseTool {
  readonly name = 'grep';
  readonly description =
    'Search file contents using a regex pattern. Uses ripgrep (rg) if available, falls back to Node.js search. ' +
    'Supports output modes: content (matching lines), files_with_matches (file paths only), count (match counts).';
  readonly isConcurrencySafe = true;

  definition(): Anthropic.Tool {
    return {
      name: this.name,
      description: this.description,
      input_schema: {
        type: 'object' as const,
        properties: {
          pattern: { type: 'string', description: 'Regex pattern to search for' },
          path: { type: 'string', description: 'File or directory to search in' },
          glob: { type: 'string', description: 'File filter glob pattern, e.g. "*.ts"' },
          output_mode: {
            type: 'string',
            enum: ['content', 'files_with_matches', 'count'],
            description: 'Output format (default: files_with_matches)',
          },
          case_insensitive: { type: 'boolean', description: 'Case insensitive search' },
          context: { type: 'number', description: 'Lines of context around each match' },
        },
        required: ['pattern'],
      },
    };
  }

  async execute(args: Record<string, unknown>): Promise<string> {
    const pattern = String(args.pattern);
    const searchPath = args.path ? String(args.path) : (this.workingDir ?? process.cwd());
    const glob = args.glob ? String(args.glob) : undefined;
    const outputMode = (args.output_mode as string) ?? 'files_with_matches';
    const caseInsensitive = Boolean(args.case_insensitive ?? false);
    const context = args.context ? Number(args.context) : undefined;

    // Try ripgrep first
    try {
      return this.runRipgrep(pattern, searchPath, glob, outputMode, caseInsensitive, context);
    } catch {
      return this.runNodeFallback(pattern, searchPath, outputMode, caseInsensitive);
    }
  }

  private runRipgrep(
    pattern: string,
    searchPath: string,
    glob: string | undefined,
    outputMode: string,
    caseInsensitive: boolean,
    context: number | undefined,
  ): string {
    const args: string[] = ['--no-heading'];
    if (caseInsensitive) args.push('-i');
    if (glob) args.push('--glob', glob);
    if (outputMode === 'files_with_matches') args.push('-l');
    if (outputMode === 'count') args.push('--count');
    if (context !== undefined) args.push('-C', String(context));
    args.push(pattern, searchPath);

    const result = child_process.spawnSync('rg', args, { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 });
    if (result.error) throw result.error;

    return result.stdout?.trim() || '(no matches)';
  }

  private runNodeFallback(
    pattern: string,
    searchPath: string,
    outputMode: string,
    caseInsensitive: boolean,
  ): string {
    const regex = new RegExp(pattern, caseInsensitive ? 'gi' : 'g');
    const results: string[] = [];

    const walk = (dir: string) => {
      try {
        for (const entry of fs.readdirSync(dir)) {
          const full = path.join(dir, entry);
          try {
            const stat = fs.statSync(full);
            if (stat.isDirectory()) {
              if (!['node_modules', '.git', 'dist'].includes(entry)) walk(full);
            } else {
              const content = fs.readFileSync(full, 'utf-8');
              const lines = content.split('\n');
              const hits = lines.filter((l) => regex.test(l));
              regex.lastIndex = 0;
              if (hits.length > 0) {
                if (outputMode === 'files_with_matches') results.push(full);
                else if (outputMode === 'count') results.push(`${full}: ${hits.length}`);
                else hits.forEach((h, i) => results.push(`${full}:${i + 1}:${h}`));
              }
            }
          } catch { /* skip unreadable */ }
        }
      } catch { /* skip unreadable dirs */ }
    };

    const stat = fs.existsSync(searchPath) ? fs.statSync(searchPath) : null;
    if (stat?.isFile()) {
      const content = fs.readFileSync(searchPath, 'utf-8');
      const hits = content.split('\n').filter((l) => regex.test(l));
      regex.lastIndex = 0;
      if (outputMode === 'files_with_matches') return hits.length ? searchPath : '(no matches)';
      return hits.join('\n') || '(no matches)';
    }
    walk(searchPath);
    return results.slice(0, 500).join('\n') || '(no matches)';
  }
}
