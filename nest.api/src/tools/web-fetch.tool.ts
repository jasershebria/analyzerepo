import axios from 'axios';
import type Anthropic from '@anthropic-ai/sdk';
import { BaseTool } from './base/base-tool';

export class WebFetchTool extends BaseTool {
  readonly name = 'web_fetch';
  readonly description = 'Fetch content from a URL and return the response as text.';
  readonly isConcurrencySafe = true;

  definition(): Anthropic.Tool {
    return {
      name: this.name,
      description: this.description,
      input_schema: {
        type: 'object' as const,
        properties: {
          url: { type: 'string', description: 'URL to fetch' },
        },
        required: ['url'],
      },
    };
  }

  async execute(args: Record<string, unknown>): Promise<string> {
    const { data } = await axios.get(String(args.url), {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      timeout: 15000,
      responseType: 'text',
    });
    return typeof data === 'string' ? data.slice(0, 50000) : JSON.stringify(data).slice(0, 50000);
  }
}
