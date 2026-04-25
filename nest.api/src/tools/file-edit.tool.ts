import * as fs from 'fs';
import * as path from 'path';
import type Anthropic from '@anthropic-ai/sdk';
import { BaseTool } from './base/base-tool';

export class FileEditTool extends BaseTool {
  readonly name = 'file_edit';
  readonly description =
    'Edit a file by replacing exact text. old_string must match exactly (including whitespace). ' +
    'Use replace_all=true to replace all occurrences.';
  readonly isConcurrencySafe = false;

  definition(): Anthropic.Tool {
    return {
      name: this.name,
      description: this.description,
      input_schema: {
        type: 'object' as const,
        properties: {
          file_path: { type: 'string', description: 'Path to the file to edit' },
          old_string: { type: 'string', description: 'Exact text to find and replace' },
          new_string: { type: 'string', description: 'Text to replace it with' },
          replace_all: { type: 'boolean', description: 'Replace all occurrences (default false)' },
        },
        required: ['file_path', 'old_string', 'new_string'],
      },
    };
  }

  async execute(args: Record<string, unknown>): Promise<string> {
    let filePath = String(args.file_path);
    const oldStr = String(args.old_string);
    const newStr = String(args.new_string);
    const replaceAll = Boolean(args.replace_all ?? false);

    if (!path.isAbsolute(filePath) && this.workingDir) {
      filePath = path.join(this.workingDir, filePath);
    }

    if (!fs.existsSync(filePath)) throw new Error(`File not found: ${filePath}`);

    const content = fs.readFileSync(filePath, 'utf-8');
    const occurrences = content.split(oldStr).length - 1;

    if (occurrences === 0) throw new Error(`old_string not found in ${filePath}`);
    if (!replaceAll && occurrences > 1) {
      throw new Error(`old_string appears ${occurrences} times — use replace_all=true or provide more context.`);
    }

    const updated = replaceAll ? content.split(oldStr).join(newStr) : content.replace(oldStr, newStr);
    fs.writeFileSync(filePath, updated, 'utf-8');
    return `Edited ${filePath} (${replaceAll ? occurrences : 1} replacement${occurrences !== 1 ? 's' : ''})`;
  }
}
