import type Anthropic from '@anthropic-ai/sdk';
import type { BaseTool } from '../../tools/base/base-tool';
import type { ThinkingConfig } from './thinking';

export interface Message {
  role: 'user' | 'assistant';
  content: string | Anthropic.ContentBlockParam[];
}

export interface QueryParams {
  messages: Message[];
  systemPrompt: string;
  tools: BaseTool[];
  model: string;
  maxTurns?: number;
  thinkingConfig?: ThinkingConfig;
  abortController?: AbortController;
}

export type AgentEvent =
  | { type: 'thinking_delta'; thinking: string }
  | { type: 'text_delta'; text: string }
  | { type: 'tool_start'; tool: string; input: unknown }
  | { type: 'plan'; tasks: unknown[] }
  | { type: 'tool_end'; tool: string; output: string }
  | { type: 'answer'; content: string }
  | { type: 'done' }
  | { type: 'error'; message: string };

export interface ToolUpdate {
  event?: AgentEvent;
  toolResult?: Anthropic.ToolResultBlockParam;
}
