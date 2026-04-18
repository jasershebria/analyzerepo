import { Injectable, inject, signal } from '@angular/core';
import { AnalysisData, GetRepositoryResponse, Message } from '../../../models/analysis.models';
import { AiChatService } from './ai-chat.service';

@Injectable()
export class AnalysisStateService {
  private readonly aiChatService = inject(AiChatService);

  readonly isConnected = signal(false);
  readonly isTyping = signal(false);
  readonly messages = signal<Message[]>([]);
  readonly analysisData = signal<AnalysisData | null>(null);

  private systemPrompt = '';

  connect(repo: GetRepositoryResponse): void {
    this.systemPrompt =
      `You are an AI assistant analyzing the repository "${repo.name}" (${repo.webUrl}). ` +
      `Default branch: ${repo.defaultBranch}. ` +
      `Help the user understand the business logic, architecture, and code flows of this codebase. ` +
      `Be concise and specific. When describing processes, use clear step-by-step explanations.`;

    this.isConnected.set(true);
    this.messages.set([
      {
        role: 'assistant',
        content: `Connected to **${repo.name}**! I'm ready to analyze your codebase. Ask me anything about the business logic, flows, or architecture.`,
      },
    ]);
    this.analysisData.set(null);
  }

  reset(): void {
    this.isConnected.set(false);
    this.isTyping.set(false);
    this.messages.set([]);
    this.analysisData.set(null);
    this.systemPrompt = '';
  }

  sendMessage(text: string): void {
    this.messages.update(msgs => [...msgs, { role: 'user', content: text }]);
    this.isTyping.set(true);

    const history = this.messages();
    const firstUserIdx = history.findIndex(m => m.role === 'user');
    const apiMessages = firstUserIdx === -1 ? [] : history.slice(firstUserIdx);

    this.aiChatService
      .chatWithHistory({
        messages: apiMessages.map(m => ({ role: m.role, content: m.content })),
        systemPrompt: this.systemPrompt,
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
  }
}
