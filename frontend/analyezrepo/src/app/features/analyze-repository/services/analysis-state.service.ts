import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, forkJoin, of } from 'rxjs';
import { catchError, switchMap, map } from 'rxjs/operators';
import { AnalysisData, GetRepositoryResponse, Message } from '../../../models/analysis.models';
import { AiChatService } from './ai-chat.service';
import { environment } from '../../../../environments/environment';

@Injectable()
export class AnalysisStateService {
  private readonly aiChatService = inject(AiChatService);
  private readonly http = inject(HttpClient);

  readonly isConnected = signal(false);
  readonly isTyping = signal(false);
  readonly messages = signal<Message[]>([]);
  readonly analysisData = signal<AnalysisData | null>(null);
  readonly isLoadingContext = signal(false);

  private systemPrompt = '';
  private repoLocalPath = 'D:\\NoxAlarmApp';
  private repoId = '';

  connect(repo: GetRepositoryResponse): void {
    const basePrompt =
      `You are an AI assistant with FULL ACCESS to the source code of the repository "${repo.name}" (${repo.webUrl}). ` +
      `Default branch: ${repo.defaultBranch}. ` +
      `The complete codebase is on this machine at D:\\NoxAlarmApp. Use tools to read and modify files directly.`;

    this.repoId = repo.id;
    this.isConnected.set(true);
    this.isLoadingContext.set(true);
    this.messages.set([
      {
        role: 'assistant',
        content: `Connected to **${repo.name}**! Reading the codebase...`,
      },
    ]);
    this.analysisData.set(null);

    this.http
      .post<{ status: string; workspacePath: string; message: string }>(`${environment.apiBase}/api/repositories/${repo.id}/sync`, {})
      .pipe(
        switchMap(syncResult =>
          this.http
            .get<{ fileTree: string[]; repoUrl: string }>(`${environment.apiBase}/api/repositories/${repo.id}/analyze`)
            .pipe(map(analysis => ({ syncResult, analysis })))
        ),
        catchError(() => of(null)),
      )
      .subscribe(result => {
        if (result) {
          const { syncResult, analysis } = result;
          const fileTreeText = analysis.fileTree.join('\n');
          this.systemPrompt = `${basePrompt}\n\nLocal workspace: ${syncResult.workspacePath}\n\nFile tree:\n${fileTreeText}`;
          this.isLoadingContext.set(false);
          const statusMsg = syncResult.status === 'error'
            ? `Sync failed: ${syncResult.message}`
            : `Sync: **${syncResult.status}**. Ready to read files from \`${syncResult.workspacePath}\`.`;
          this.messages.set([{
            role: 'assistant',
            content: `Connected to **${repo.name}**! ${statusMsg}`,
          }]);
        } else {
          this.systemPrompt = basePrompt;
          this.isLoadingContext.set(false);
          this.messages.set([{
            role: 'assistant',
            content: `Connected to **${repo.name}**! (Could not sync — answering from repo metadata only.)`,
          }]);
        }
      });
  }

  reset(): void {
    this.isConnected.set(false);
    this.isTyping.set(false);
    this.messages.set([]);
    this.analysisData.set(null);
    this.systemPrompt = '';
  }

  sendMessage(text: string): void {
    if (this.isLoadingContext()) return;
    this.messages.update(msgs => [...msgs, { role: 'user', content: text }]);
    this.isTyping.set(true);

    this._enrichWithFiles(text).subscribe(enrichedText => {
      const history = this.messages();
      const firstUserIdx = history.findIndex(m => m.role === 'user');
      const apiMessages = firstUserIdx === -1 ? [] : history.slice(firstUserIdx);
      // Replace last user message with enriched version
      const messagesForApi = apiMessages.map((m, i) =>
        i === apiMessages.length - 1 && m.role === 'user'
          ? { role: m.role, content: enrichedText }
          : { role: m.role, content: m.content }
      );

      this.aiChatService
        .chatWithHistory({
          messages: messagesForApi,
          systemPrompt: this.systemPrompt,
          repoId: this.repoId,
        })
        .subscribe({
          next: res => {
            this.messages.update(msgs => [
              ...msgs,
              { role: 'assistant', content: res.reply },
            ]);
            this.isTyping.set(false);
          },
          error: () => {
            this.messages.update(msgs => [
              ...msgs,
              { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' },
            ]);
            this.isTyping.set(false);
          },
        });
    });
  }

  private _enrichWithFiles(text: string): Observable<string> {
    // Full absolute paths: D:\...\file.ext
    const absPathRegex = /([A-Za-z]:\\[\w\\.\-]+\.\w+)/g;
    // Relative paths with at least one dir: src/path/file.ext
    const relPathRegex = /(?:[\w\-]+\/)+[\w.\-]+\.\w{2,5}/g;
    // Bare filenames with known code extensions
    const bareFileRegex = /\b([\w\-]+\.(?:ts|tsx|js|jsx|py|cs|json|yaml|yml|md|scss|css|html|toml|txt))\b/g;

    const fullPaths = new Set<string>([
      ...(text.match(absPathRegex) ?? []),
      ...(text.match(relPathRegex) ?? []).map(p =>
        this.repoLocalPath ? `${this.repoLocalPath}\\${p.replace(/\//g, '\\')}` : p
      ),
      ...(text.match(bareFileRegex) ?? []).map(f =>
        this.repoLocalPath ? `${this.repoLocalPath}\\${f}` : f
      ),
    ]);

    const matches = [...fullPaths];
    if (matches.length === 0) return of(text);

    // Fetch each file — fall back to /find (searches by name) if direct path returns 404
    const reads = matches.map(p =>
      this.http
        .get<{ path: string; content: string }>(
          `${environment.apiBase}/api/files/read?path=${encodeURIComponent(p)}`
        )
        .pipe(
          catchError(() => {
            const name = p.split(/[\\/]/).pop() ?? p;
            return this.http
              .get<{ path: string; content: string }>(
                `${environment.apiBase}/api/files/find?name=${encodeURIComponent(name)}`
              )
              .pipe(catchError(() => of(null)));
          })
        )
    );

    return new Observable<string>(obs => {
      forkJoin(reads).subscribe(results => {
        const snippets = (results as ({ path: string; content: string } | null)[])
          .filter((r): r is { path: string; content: string } => r !== null)
          .map(r => `=== ${r.path} ===\n\`\`\`\n${r.content}\n\`\`\``)
          .join('\n\n');

        // Put file content BEFORE the question so the model sees it first
        const enriched = snippets ? `${snippets}\n\nUser question: ${text}` : text;
        obs.next(enriched);
        obs.complete();
      });
    });
  }
}
