import * as fs from 'fs';
import * as path from 'path';
import type Anthropic from '@anthropic-ai/sdk';
import { BaseTool } from './base/base-tool';

export class FileWriteTool extends BaseTool {
  readonly name = 'file_write';
  readonly description = 'Write content to a file, creating directories as needed. Overwrites existing file.';
  readonly isConcurrencySafe = false;

  definition(): Anthropic.Tool {
    return {
      name: this.name,
      description: this.description,
      input_schema: {
        type: 'object' as const,
        properties: {
          file_path: { type: 'string', description: 'Path to the file to write' },
          content: { type: 'string', description: 'Content to write' },
        },
        required: ['file_path', 'content'],
      },
    };
  }

  async execute(args: Record<string, unknown>): Promise<string> {
    let filePath = String(args.file_path);
    const content = String(args.content);

    if (!path.isAbsolute(filePath) && this.workingDir) {
      filePath = path.join(this.workingDir, filePath);
    }

    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, content, 'utf-8');
    return `Written ${content.split('\n').length} lines to ${filePath}`;
  }
}
