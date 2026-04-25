import { Injectable } from '@nestjs/common';
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import { VectorStoreService, RagChunk } from './vector-store.service';

const CHUNK_SIZE = 1000;
const CHUNK_OVERLAP = 200;
const IGNORE_DIRS = new Set(['node_modules', '.git', 'dist', '__pycache__', '.next', 'build']);
const TEXT_EXTENSIONS = new Set([
  '.ts', '.tsx', '.js', '.jsx', '.py', '.java', '.cs', '.go', '.rs',
  '.cpp', '.c', '.h', '.hpp', '.rb', '.php', '.swift', '.kt',
  '.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.xml', '.html', '.css', '.scss',
]);

@Injectable()
export class IndexingService {
  constructor(private readonly vectorStore: VectorStoreService) {}

  async buildIndex(workspaceDir: string, repoId: string, force = false): Promise<{ indexed: number }> {
    if (!force) {
      const existing = await this.vectorStore.countChunks(repoId);
      if (existing > 0) return { indexed: existing };
    }

    const files = this.walkDir(workspaceDir);
    const chunks: RagChunk[] = [];

    for (const filePath of files) {
      try {
        const content = fs.readFileSync(filePath, 'utf-8');
        const relPath = path.relative(workspaceDir, filePath);
        const fileChunks = this.chunkText(content, CHUNK_SIZE, CHUNK_OVERLAP);

        for (let i = 0; i < fileChunks.length; i++) {
          const chunkContent = fileChunks[i];
          const chunkId = crypto
            .createHash('md5')
            .update(`${repoId}:${relPath}:${i}`)
            .digest('hex');

          const embedding = await this.vectorStore.embed(chunkContent);
          chunks.push({ chunkId, content: chunkContent, embedding, metadata: { filePath: relPath, chunkIndex: i } });

          if (chunks.length >= 50) {
            await this.vectorStore.upsertChunks(repoId, chunks.splice(0, 50));
          }
        }
      } catch { /* skip unreadable files */ }
    }

    if (chunks.length) await this.vectorStore.upsertChunks(repoId, chunks);
    return { indexed: await this.vectorStore.countChunks(repoId) };
  }

  private walkDir(dir: string): string[] {
    const results: string[] = [];
    try {
      for (const entry of fs.readdirSync(dir)) {
        if (IGNORE_DIRS.has(entry)) continue;
        const full = path.join(dir, entry);
        try {
          const stat = fs.statSync(full);
          if (stat.isDirectory()) results.push(...this.walkDir(full));
          else if (TEXT_EXTENSIONS.has(path.extname(entry).toLowerCase())) results.push(full);
        } catch { /* skip */ }
      }
    } catch { /* skip unreadable dirs */ }
    return results;
  }

  private chunkText(text: string, size: number, overlap: number): string[] {
    const chunks: string[] = [];
    let start = 0;
    while (start < text.length) {
      chunks.push(text.slice(start, start + size));
      start += size - overlap;
    }
    return chunks.filter((c) => c.trim().length > 0);
  }
}
