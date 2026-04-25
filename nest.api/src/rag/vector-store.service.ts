import { Injectable } from '@nestjs/common';
import { InjectConnection } from '@nestjs/mongoose';
import { Connection } from 'mongoose';
import { ConfigService } from '@nestjs/config';
import axios from 'axios';

export interface RagChunk {
  chunkId: string;
  content: string;
  embedding: number[];
  metadata: { filePath: string; [key: string]: unknown };
}

@Injectable()
export class VectorStoreService {
  constructor(
    @InjectConnection() private readonly connection: Connection,
    private readonly config: ConfigService,
  ) {}

  private collectionName(repoId: string): string {
    return `rag_chunks_${repoId.replace(/-/g, '_')}`;
  }

  async embed(text: string): Promise<number[]> {
    const baseUrl = this.config.get<string>('embedding.baseUrl');
    const model = this.config.get<string>('embedding.model');
    const { data } = await axios.post(`${baseUrl}/api/embeddings`, { model, prompt: text }, { timeout: 30000 });
    return data.embedding as number[];
  }

  async upsertChunks(repoId: string, chunks: RagChunk[]): Promise<void> {
    const col = this.connection.db!.collection(this.collectionName(repoId));
    const ops = chunks.map((chunk) => ({
      updateOne: {
        filter: { chunkId: chunk.chunkId },
        update: { $set: chunk },
        upsert: true,
      },
    }));
    if (ops.length) await col.bulkWrite(ops);
  }

  async similaritySearch(
    repoId: string,
    query: string,
    topK: number,
  ): Promise<Array<RagChunk & { score: number }>> {
    const queryEmbedding = await this.embed(query);
    const col = this.connection.db!.collection(this.collectionName(repoId));
    const docs = await col.find({}).limit(20000).toArray();

    const scored = docs.map((doc) => ({
      ...(doc as unknown as RagChunk),
      score: cosineSimilarity(queryEmbedding, doc.embedding as number[]),
    }));

    return scored.sort((a, b) => b.score - a.score).slice(0, topK);
  }

  async countChunks(repoId: string): Promise<number> {
    const col = this.connection.db!.collection(this.collectionName(repoId));
    return col.countDocuments();
  }
}

function cosineSimilarity(a: number[], b: number[]): number {
  if (!a?.length || !b?.length || a.length !== b.length) return 0;
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] ** 2;
    normB += b[i] ** 2;
  }
  const denom = Math.sqrt(normA) * Math.sqrt(normB);
  return denom === 0 ? 0 : dot / denom;
}
