// Ported from claude-code/src/utils/thinking.ts

export type ThinkingConfig =
  | { type: 'adaptive' }
  | { type: 'enabled'; budgetTokens: number }
  | { type: 'disabled' };

export function getThinkingConfig(model: string, maxTokens?: number): ThinkingConfig {
  if (!maxTokens || maxTokens <= 0) return { type: 'disabled' };
  if (modelSupportsThinking(model)) return { type: 'enabled', budgetTokens: maxTokens };
  return { type: 'disabled' };
}

export function modelSupportsThinking(model: string): boolean {
  // Claude 4+ and claude-3-7+ support extended thinking
  return (
    model.includes('claude-') &&
    !model.includes('claude-3-haiku') &&
    !model.includes('claude-3-sonnet') &&
    !model.includes('claude-3-opus') &&
    !model.includes('claude-instant')
  );
}
