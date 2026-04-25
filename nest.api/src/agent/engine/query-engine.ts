// Ported from claude-code/src/QueryEngine.ts
// Owns submitMessage() → async generator of AgentEvents
// Maintains conversation state across turns

import Anthropic from '@anthropic-ai/sdk';
import { queryLoop } from './query';
import { getThinkingConfig, ThinkingConfig } from './thinking';
import type { AgentEvent, Message } from './types';
import type { BaseTool } from '../../tools/base/base-tool';

export interface QueryEngineOptions {
  systemPrompt: string;
  tools: BaseTool[];
  model: string;
  apiKey: string;
  baseURL?: string;
  maxTurns?: number;
  maxThinkingTokens?: number;
}

export class QueryEngine {
  private readonly client: Anthropic;
  private readonly systemPrompt: string;
  private readonly tools: BaseTool[];
  private readonly model: string;
  private readonly maxTurns: number;
  private readonly thinkingConfig: ThinkingConfig;
  private mutableMessages: Message[] = [];
  private abortController = new AbortController();

  constructor(opts: QueryEngineOptions) {
    this.client = new Anthropic({ apiKey: opts.apiKey, baseURL: opts.baseURL });
    this.systemPrompt = opts.systemPrompt;
    this.tools = opts.tools;
    this.model = opts.model;
    this.maxTurns = opts.maxTurns ?? 15;
    this.thinkingConfig = getThinkingConfig(opts.model, opts.maxThinkingTokens);
  }

  withHistory(history: Message[]): void {
    this.mutableMessages = [...history];
  }

  abort(): void {
    this.abortController.abort();
  }

  async *submitMessage(prompt: string): AsyncGenerator<AgentEvent> {
    const userMessage: Message = { role: 'user', content: prompt };
    this.mutableMessages.push(userMessage);

    yield* queryLoop(
      {
        messages: [...this.mutableMessages],
        systemPrompt: this.systemPrompt,
        tools: this.tools,
        model: this.model,
        maxTurns: this.maxTurns,
        thinkingConfig: this.thinkingConfig,
        abortController: this.abortController,
      },
      this.client,
    );
  }
}
