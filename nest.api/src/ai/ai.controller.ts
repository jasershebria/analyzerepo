import { Body, Controller, Get, Post } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { AiService } from './ai.service';
import { ChatWithHistoryDto } from './dto/ai.dto';

@ApiTags('AI')
@Controller('api/ai')
export class AiController {
  constructor(private readonly svc: AiService) {}

  @Get('test-connection')
  @ApiOperation({ summary: 'Test LLM connectivity' })
  testConnection() {
    return this.svc.testConnection();
  }

  @Post('chat/history')
  @ApiOperation({ summary: 'Multi-turn chat with optional tool calling' })
  async chatWithHistory(@Body() dto: ChatWithHistoryDto) {
    const reply = await this.svc.chatWithHistory(dto.messages, dto.systemPrompt);
    return { reply };
  }
}
