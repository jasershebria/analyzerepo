import { Injectable, signal, computed } from '@angular/core';
import { AgentStreamService, AgentEvent, TodoItem } from './agent-stream.service';

export interface ToolCall {
  id: string;
  tool: string;
  input: Record<string, unknown>;
  output?: string;
  status: 'pending' | 'done';
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls: ToolCall[];
  plan: TodoItem[] | null;
  isStreaming: boolean;
}

@Injectable()
export class AgentStateService {
  private readonly streamSvc = new AgentStreamService();

  readonly messages = signal<ChatMessage[]>([]);
  readonly isStreaming = signal(false);
  readonly repoId = signal<string>('');

  readonly hasMessages = computed(() => this.messages().length > 0);

  sendMessage(text: string): void {
    if (!text.trim() || this.isStreaming()) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      toolCalls: [],
      plan: null,
      isStreaming: false,
    };

    const assistantMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      toolCalls: [],
      plan: null,
      isStreaming: true,
    };

    this.messages.update(msgs => [...msgs, userMsg, assistantMsg]);
    this.isStreaming.set(true);

    const history = this.messages()
      .slice(0, -2)
      .map(m => ({ role: m.role, content: m.content }));

    this.streamSvc
      .stream({ prompt: text, repoId: this.repoId() || undefined, history })
      .subscribe({
        next: (event: AgentEvent) => this._handleEvent(event, assistantMsg.id),
        error: () => {
          this._updateAssistant(assistantMsg.id, msg => ({
            ...msg,
            content: msg.content || 'An error occurred. Please try again.',
            isStreaming: false,
          }));
          this.isStreaming.set(false);
        },
        complete: () => {
          this._updateAssistant(assistantMsg.id, msg => ({ ...msg, isStreaming: false }));
          this.isStreaming.set(false);
        },
      });
  }

  private _handleEvent(event: AgentEvent, assistantId: string): void {
    switch (event.type) {
      case 'token':
        this._updateAssistant(assistantId, msg => ({
          ...msg,
          content: msg.content + event.content,
        }));
        break;

      case 'answer':
        this._updateAssistant(assistantId, msg => ({
          ...msg,
          content: event.content,
        }));
        break;

      case 'tool_start':
        this._updateAssistant(assistantId, msg => ({
          ...msg,
          toolCalls: [
            ...msg.toolCalls,
            { id: crypto.randomUUID(), tool: event.tool, input: event.input, status: 'pending' },
          ],
        }));
        break;

      case 'tool_end': {
        this._updateAssistant(assistantId, msg => {
          const calls = [...msg.toolCalls];
          const idx = [...calls].map((c: ToolCall) => c).reduceRight((found, c, i) => found === -1 && c.tool === event.tool && c.status === 'pending' ? i : found, -1);
          if (idx !== -1) {
            calls[idx] = { ...calls[idx], output: event.output, status: 'done' };
          }
          return { ...msg, toolCalls: calls };
        });
        break;
      }

      case 'plan':
        this._updateAssistant(assistantId, msg => ({ ...msg, plan: event.tasks }));
        break;
    }
  }

  private _updateAssistant(id: string, fn: (m: ChatMessage) => ChatMessage): void {
    this.messages.update(msgs => msgs.map(m => (m.id === id ? fn(m) : m)));
  }

  clearMessages(): void {
    this.messages.set([]);
  }
}
