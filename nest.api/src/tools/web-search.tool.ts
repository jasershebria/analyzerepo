import axios from 'axios';
import type Anthropic from '@anthropic-ai/sdk';
import { BaseTool } from './base/base-tool';

export class WebSearchTool extends BaseTool {
  readonly name = 'web_search';
  readonly description = 'Search the web using DuckDuckGo and return top results.';
  readonly isConcurrencySafe = true;

  definition(): Anthropic.Tool {
    return {
      name: this.name,
      description: this.description,
      input_schema: {
        type: 'object' as const,
        properties: {
          query: { type: 'string', description: 'Search query' },
        },
        required: ['query'],
      },
    };
  }

  async execute(args: Record<string, unknown>): Promise<string> {
    const query = encodeURIComponent(String(args.query));
    const { data } = await axios.get(
      `https://api.duckduckgo.com/?q=${query}&format=json&no_html=1&skip_disambig=1`,
      { timeout: 10000 },
    );
    const results: string[] = [];
    if (data.AbstractText) results.push(`Summary: ${data.AbstractText}`);
    for (const r of data.RelatedTopics?.slice(0, 5) ?? []) {
      if (r.Text) results.push(`• ${r.Text}`);
    }
    return results.join('\n') || 'No results found.';
  }
}
