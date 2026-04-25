import * as fs from 'fs';
import * as path from 'path';
import type Anthropic from '@anthropic-ai/sdk';
import { BaseTool } from './base/base-tool';

// Ported from claude-code FileReadTool — blocked device paths for security
const BLOCKED_PATHS = new Set(['/dev/null', '/dev/zero', '/dev/random', '/dev/urandom']);

export class FileReadTool extends BaseTool {
  readonly name = 'file_read';
  readonly description =
    'Read a file from the filesystem. Returns the file contents with line numbers. ' +
    'Use offset and limit to read specific line ranges of large files.';
  readonly isConcurrencySafe = true;

  definition(): Anthropic.Tool {
    return {
      name: this.name,
      description: this.description,
      input_schema: {
        type: 'object' as const,
        properties: {
          file_path: { type: 'string', description: 'Absolute or relative path to the file' },
          offset: { type: 'number', description: 'Line number to start reading from (0-indexed)' },
          limit: { type: 'number', description: 'Maximum number of lines to read' },
        },
        required: ['file_path'],
      },
    };
  }

  async execute(args: Record<string, unknown>): Promise<string> {
    let filePath = String(args.file_path);
    const offset = args.offset ? Number(args.offset) : 0;
    const limit = args.limit ? Number(args.limit) : undefined;

    if (!path.isAbsolute(filePath) && this.workingDir) {
      filePath = path.join(this.workingDir, filePath);
    }

    if (BLOCKED_PATHS.has(filePath)) {
      throw new Error(`Access to '${filePath}' is not allowed.`);
    }

    if (!fs.existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) {
      throw new Error(`'${filePath}' is a directory, not a file.`);
    }

    const raw = fs.readFileSync(filePath, 'utf-8');
    const lines = raw.split('\n');
    const sliced = limit !== undefined ? lines.slice(offset, offset + limit) : lines.slice(offset);

    // cat -n format: "1\t<line>"
    return sliced
      .map((line, i) => `${offset + i + 1}\t${line}`)
      .join('\n');
  }
}
