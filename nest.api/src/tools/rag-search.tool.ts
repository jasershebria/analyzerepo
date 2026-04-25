import type Anthropic from '@anthropic-ai/sdk';
import { BaseTool } from './base/base-tool';

export type RagSearchFn = (repoId: string, query: string, topK: number) => Promise<Array<{ content: string; metadata: any; score: number }>>;

export class RagSearchTool extends BaseTool {
  readonly name = 'rag_search';
  readonly description =
    'Search the indexed codebase using semantic similarity. Returns relevant code snippets from the repository.';
  readonly isConcurrencySafe = true;

  constructor(workingDir?: string, private readonly searchFn?: RagSearchFn) {
    super(workingDir);
  }

  definition(): Anthropic.Tool {
    return {
      name: this.name,
      description: this.description,
      input_schema: {
        type: 'object' as const,
        properties: {
          query: { type: 'string', description: 'Natural language query about the codebase' },
          repo_id: { type: 'string', description: 'Repository ID to search in' },
          top_k: { type: 'number', description: 'Number of results to return (default 5)' },
        },
        required: ['query', 'repo_id'],
      },
    };
  }

  async execute(args: Record<string, unknown>): Promise<string> {
    if (!this.searchFn) return 'RAG search not available (no index configured).';

    const query = String(args.query);
    const repoId = String(args.repo_id);
    const topK = Number(args.top_k ?? 5);

    const results = await this.searchFn(repoId, query, topK);
    if (!results.length) return 'No relevant results found.';

    return results
      .map((r) => `// ${r.metadata?.filePath ?? 'unknown'} (score: ${r.score.toFixed(3)})\n${r.content}`)
      .join('\n\n---\n\n');
  }
}
