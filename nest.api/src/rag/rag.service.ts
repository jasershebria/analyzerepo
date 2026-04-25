import { Injectable } from '@nestjs/common';
import { VectorStoreService } from './vector-store.service';
import { AiService } from '../ai/ai.service';
import { QueryRagDto, QueryRagResponse } from './dto/rag.dto';

@Injectable()
export class RagService {
  constructor(
    private readonly vectorStore: VectorStoreService,
    private readonly ai: AiService,
  ) {}

  async query(dto: QueryRagDto): Promise<QueryRagResponse> {
    const results = await this.vectorStore.similaritySearch(dto.repoId, dto.question, dto.topK ?? 5);

    if (!results.length) {
      return { answer: 'No relevant code found in the index for this repository.', sources: [] };
    }

    const context = results
      .map((r, i) => `[${i + 1}] File: ${r.metadata.filePath}\n${r.content}`)
      .join('\n\n---\n\n');

    const systemPrompt = `You are a code analysis assistant. Answer the question based on the provided code context.
Be precise and reference specific files when relevant. If the context is insufficient, say so clearly.`;

    const prompt = `Context from codebase:\n${context}\n\nQuestion: ${dto.question}`;
    const answer = await this.ai.chat(prompt, systemPrompt);

    return {
      answer,
      sources: results.map((r) => ({ filePath: r.metadata.filePath, score: r.score })),
    };
  }
}
