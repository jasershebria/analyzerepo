import type Anthropic from '@anthropic-ai/sdk';

export abstract class BaseTool {
  abstract readonly name: string;
  abstract readonly description: string;
  readonly isConcurrencySafe: boolean = true;

  constructor(protected readonly workingDir?: string) {}

  abstract definition(): Anthropic.Tool;

  abstract execute(args: Record<string, unknown>): Promise<string>;

  async call(args: Record<string, unknown>): Promise<string> {
    try {
      const result = await this.execute(args);
      return result ?? '';
    } catch (e) {
      throw e;
    }
  }
}
