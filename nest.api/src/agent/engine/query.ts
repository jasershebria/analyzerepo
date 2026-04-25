// Ported from claude-code/src/query.ts — queryLoop() while(true) with mutable state
// Uses native Anthropic SDK tool_use blocks + thinking tokens

import Anthropic from '@anthropic-ai/sdk';
import { runTools } from '../orchestration/tool-orchestration';
import type { AgentEvent, Message, QueryParams, ToolUpdate } from './types';

interface State {
  messages: Message[];
  turnCount: number;
  maxOutputTokensOverride?: number;
}

export async function* queryLoop(params: QueryParams, client: Anthropic): AsyncGenerator<AgentEvent> {
  let state: State = { messages: params.messages, turnCount: 1 };

  while (true) {
    const { messages, turnCount, maxOutputTokensOverride } = state;

    if (params.abortController?.signal.aborted) {
      yield { type: 'error', message: 'Aborted by user.' };
      return;
    }

    const anthropicMessages = toAnthropicMessages(messages);
    const tools: Anthropic.Tool[] = params.tools.map((t) => t.definition());

    const thinkingParam =
      params.thinkingConfig?.type === 'enabled'
        ? { type: 'enabled' as const, budget_tokens: params.thinkingConfig.budgetTokens }
        : undefined;

    // ── Phase: Stream API response ────────────────────────────────────────────
    const assistantBlocks: Anthropic.ContentBlock[] = [];
    const toolUseBlocks: Anthropic.ToolUseBlock[] = [];
    let needsFollowUp = false;
    let stopReason: string | null = null;

    try {
      const streamParams: Anthropic.MessageStreamParams = {
        model: params.model,
        max_tokens: maxOutputTokensOverride ?? 8096,
        system: params.systemPrompt,
        tools,
        messages: anthropicMessages,
        ...(thinkingParam ? { thinking: thinkingParam } : {}),
      };

      const stream = client.messages.stream(streamParams);

      for await (const event of stream) {
        if (event.type === 'content_block_delta') {
          if (event.delta.type === 'thinking_delta') {
            yield { type: 'thinking_delta', thinking: event.delta.thinking };
          }
          if (event.delta.type === 'text_delta') {
            yield { type: 'text_delta', text: event.delta.text };
          }
        }
      }

      const finalMessage = await stream.finalMessage();
      stopReason = finalMessage.stop_reason;

      for (const block of finalMessage.content) {
        assistantBlocks.push(block);
        if (block.type === 'tool_use') {
          toolUseBlocks.push(block);
          needsFollowUp = true;
        }
      }
    } catch (e) {
      yield { type: 'error', message: (e as Error).message };
      return;
    }

    // ── Recovery: escalate max_tokens and retry (same as claude-code pattern) ──
    if (stopReason === 'max_tokens' && !maxOutputTokensOverride) {
      state = { ...state, maxOutputTokensOverride: 16384 };
      continue;
    }

    // ── No tools needed — final answer ────────────────────────────────────────
    if (!needsFollowUp) {
      const text = assistantBlocks
        .filter((b) => b.type === 'text')
        .map((b) => (b as Anthropic.TextBlock).text)
        .join('');
      yield { type: 'answer', content: text };
      return;
    }

    // ── Execute tools (partition into concurrent-safe vs serial) ──────────────
    const toolResults: Anthropic.ToolResultBlockParam[] = [];

    for await (const update of runTools(toolUseBlocks, params.tools)) {
      if (update.event) yield update.event;
      if (update.toolResult) toolResults.push(update.toolResult);
    }

    // ── Max turns guard ───────────────────────────────────────────────────────
    if (params.maxTurns && turnCount >= params.maxTurns) {
      yield { type: 'answer', content: 'Reached maximum turns without completing the task.' };
      return;
    }

    // ── Feed tool results back — update mutable state and loop ────────────────
    state = {
      messages: [
        ...messages,
        { role: 'assistant', content: assistantBlocks },
        { role: 'user', content: toolResults },
      ],
      turnCount: turnCount + 1,
    };
  }
}

function toAnthropicMessages(messages: Message[]): Anthropic.MessageParam[] {
  return messages.map((m) => ({
    role: m.role,
    content: m.content as string | Anthropic.ContentBlockParam[],
  }));
}
