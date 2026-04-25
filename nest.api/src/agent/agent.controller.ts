import { Body, Controller, Get, MessageEvent, Post, Sse } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { Observable } from 'rxjs';
import { AgentService } from './agent.service';
import { AiService } from '../ai/ai.service';
import { AgentRunDto } from './dto/agent.dto';

const FRIENDLY_SYSTEM =
  'You are a helpful AI assistant for a code repository analysis tool. Be warm, friendly, and brief.';

@ApiTags('Agent')
@Controller('api/agent')
export class AgentController {
  constructor(
    private readonly agentSvc: AgentService,
    private readonly aiSvc: AiService,
  ) {}

  @Post('run')
  @Sse()
  @ApiOperation({ summary: 'Stream agent execution events as SSE' })
  runAgent(@Body() dto: AgentRunDto): Observable<MessageEvent> {
    return new Observable((observer) => {
      (async () => {
        // Conversational shortcut — no tools needed
        if (this.agentSvc.isConversational(dto.prompt)) {
          const reply = await this.aiSvc.chat(dto.prompt, FRIENDLY_SYSTEM);
          observer.next({ data: JSON.stringify({ type: 'answer', content: reply }) } as MessageEvent);
          observer.next({ data: JSON.stringify({ type: 'done' }) } as MessageEvent);
          observer.complete();
          return;
        }

        const engine = this.agentSvc.buildEngine(dto);

        for await (const event of engine.submitMessage(dto.prompt)) {
          observer.next({ data: JSON.stringify(event) } as MessageEvent);
        }

        observer.next({ data: JSON.stringify({ type: 'done' }) } as MessageEvent);
        observer.complete();
      })().catch((err: Error) => {
        observer.next({ data: JSON.stringify({ type: 'error', message: err.message }) } as MessageEvent);
        observer.complete();
      });
    });
  }

  @Get('skills')
  @ApiOperation({ summary: 'List available skills (slash commands)' })
  listSkills() {
    return this.agentSvc.loadSkills();
  }
}
