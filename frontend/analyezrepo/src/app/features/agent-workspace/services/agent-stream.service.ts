import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface AgentRunRequest {
  prompt: string;
  repoId?: string;
  history?: AgentMessage[];
  maxRounds?: number;
}

export interface AgentMessage {
  role: string;
  content?: string;
  toolCallId?: string;
}

export type AgentEvent =
  | { type: 'token';      content: string }
  | { type: 'tool_start'; tool: string; input: Record<string, unknown> }
  | { type: 'tool_end';   tool: string; output: string }
  | { type: 'plan';       tasks: TodoItem[] }
  | { type: 'answer';     content: string }
  | { type: 'error';      message: string }
  | { type: 'done' };

export interface TodoItem {
  id?: string;
  content: string;
  status: 'pending' | 'in_progress' | 'completed';
  priority?: string;
}

@Injectable({ providedIn: 'root' })
export class AgentStreamService {
  private readonly baseUrl = `${environment.apiBase}/api/agent/run`;

  stream(request: AgentRunRequest): Observable<AgentEvent> {
    return new Observable(observer => {
      const controller = new AbortController();

      const body = {
        prompt: request.prompt,
        repoId: request.repoId ?? null,
        history: request.history ?? [],
        maxRounds: request.maxRounds ?? 15,
      };

      fetch(this.baseUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      })
        .then(async response => {
          if (!response.ok) {
            observer.error(new Error(`HTTP ${response.status}`));
            return;
          }

          const reader = response.body!.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() ?? '';

            for (const line of lines) {
              if (!line.startsWith('data: ')) continue;
              try {
                const event: AgentEvent = JSON.parse(line.slice(6));
                observer.next(event);
                if (event.type === 'done') {
                  observer.complete();
                  return;
                }
              } catch {
                // skip malformed line
              }
            }
          }
          observer.complete();
        })
        .catch(err => {
          if (err.name !== 'AbortError') observer.error(err);
        });

      return () => controller.abort();
    });
  }
}
