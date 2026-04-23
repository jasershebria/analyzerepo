import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, forkJoin, of } from 'rxjs';
import { catchError, switchMap, map } from 'rxjs/operators';
import { AnalysisData, GetRepositoryResponse, Message } from '../../../models/analysis.models';
import { RagService } from './rag.service';
import { environment } from '../../../../environments/environment';

@Injectable()
export class AnalysisStateService {
  private readonly ragService = inject(RagService);
  private readonly http = inject(HttpClient);

  readonly isConnected = signal(false);
  readonly isTyping = signal(false);
  readonly messages = signal<Message[]>([]);
  readonly analysisData = signal<AnalysisData | null>(null);
  readonly isLoadingContext = signal(false);

  private repoLocalPath = 'D:\\NoxAlarmApp';
  private repoId = '';
  private workspacePath = '';
  private sessionId = '';

  connect(repo: GetRepositoryResponse): void {
    this.repoId = repo.id;
    this.sessionId = `${repo.id}-${Date.now()}`;
    this.isConnected.set(true);
    this.isLoadingContext.set(true);
    this.messages.set([
      { role: 'assistant', content: `Connected to **${repo.name}**! Syncing and indexing...` },
    ]);
    this.analysisData.set(null);

    this.http
      .post<{ status: string; workspacePath: string; message: string }>(
        `${environment.apiBase}/api/repositories/${repo.id}/sync`, {}
      )
      .pipe(
        switchMap(syncResult => {
          this.workspacePath = syncResult.workspacePath;

          const analyze$ = this.http
            .get<{ fileTree: string[]; repoUrl: string }>(
              `${environment.apiBase}/api/repositories/${repo.id}/analyze`
            )
            .pipe(catchError(() => of({ fileTree: [], repoUrl: '' })));

          return forkJoin({ syncResult: of(syncResult), analysis: analyze$ });
        }),
        catchError(() => of(null)),
      )
      .subscribe(result => {
        this.isLoadingContext.set(false);

        if (!result) {
          this.messages.set([
            { role: 'assistant', content: `Connected to **${repo.name}**. (Sync failed — limited functionality.)` },
          ]);
          return;
        }

        const { syncResult } = result;
        const syncStatus = syncResult.status === 'error'
          ? `Sync failed: ${syncResult.message}`
          : `Sync: **${syncResult.status}**.`;

        this.messages.set([
          {
            role: 'assistant',
            content: `Connected to **${repo.name}**! ${syncStatus}\n\nAsk me anything about the codebase.`,
          },
        ]);
      });
  }

  reset(): void {
    this.isConnected.set(false);
    this.isTyping.set(false);
    this.messages.set([]);
    this.analysisData.set(null);
    this.repoId = '';
    this.workspacePath = '';
    this.sessionId = '';
  }

  sendMessage(text: string): void {
    if (this.isLoadingContext()) return;
    this.messages.update(msgs => [...msgs, { role: 'user', content: text }]);
    this.isTyping.set(true);

    this.ragService
      .query({
        repoId: this.repoId,
        question: text,
        sessionId: this.sessionId,
        topK: 6,
      })
      .subscribe({
        next: res => {
          this.messages.update(msgs => [
            ...msgs,
            { role: 'assistant', content: res.answer },
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
  }
}
