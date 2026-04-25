import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import Anthropic from '@anthropic-ai/sdk';
import { ChatMessageDto } from './dto/ai.dto';

@Injectable()
export class AiService {
  private client: Anthropic;
  private model: string;

  constructor(private readonly config: ConfigService) {
    this.client = new Anthropic({
      apiKey: this.config.get<string>('ai.apiKey'),
      baseURL: this.config.get<string>('ai.baseUrl'),
    });
    this.model = this.config.get<string>('ai.model') ?? 'claude-sonnet-4-6';
  }

  async testConnection(): Promise<{ success: boolean; model: string }> {
    try {
      await this.client.messages.create({
        model: this.model,
        max_tokens: 10,
        messages: [{ role: 'user', content: 'ping' }],
      });
      return { success: true, model: this.model };
    } catch {
      return { success: false, model: this.model };
    }
  }

  async chat(prompt: string, systemPrompt?: string): Promise<string> {
    const resp = await this.client.messages.create({
      model: this.model,
      max_tokens: 1024,
      system: systemPrompt,
      messages: [{ role: 'user', content: prompt }],
    });
    return resp.content.filter((b) => b.type === 'text').map((b) => (b as any).text).join('');
  }

  async chatWithHistory(messages: ChatMessageDto[], systemPrompt?: string): Promise<string> {
    const sysMsg = systemPrompt ?? messages.find((m) => m.role === 'system')?.content;
    const turns = messages
      .filter((m) => m.role !== 'system')
      .map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }));

    const resp = await this.client.messages.create({
      model: this.model,
      max_tokens: 4096,
      system: sysMsg,
      messages: turns,
    });
    return resp.content.filter((b) => b.type === 'text').map((b) => (b as any).text).join('');
  }
}
