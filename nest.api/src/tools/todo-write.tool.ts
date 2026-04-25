import type Anthropic from '@anthropic-ai/sdk';
import { BaseTool } from './base/base-tool';

export class TodoWriteTool extends BaseTool {
  readonly name = 'todo_write';
  readonly description =
    'Create a task checklist for a multi-step operation. Call this first for complex tasks to show a plan.';
  readonly isConcurrencySafe = false;

  definition(): Anthropic.Tool {
    return {
      name: this.name,
      description: this.description,
      input_schema: {
        type: 'object' as const,
        properties: {
          todos: {
            type: 'array',
            description: 'List of tasks',
            items: {
              type: 'object',
              properties: {
                content: { type: 'string', description: 'Task description' },
                status: { type: 'string', enum: ['pending', 'in_progress', 'completed'] },
              },
              required: ['content', 'status'],
            },
          },
        },
        required: ['todos'],
      },
    };
  }

  async execute(args: Record<string, unknown>): Promise<string> {
    const todos = (args.todos as any[]) ?? [];
    const lines = todos.map((t) => {
      const icon = t.status === 'completed' ? '✓' : t.status === 'in_progress' ? '→' : '○';
      return `${icon} ${t.content}`;
    });
    return `Task plan:\n${lines.join('\n')}`;
  }
}
