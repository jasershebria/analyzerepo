import { Module } from '@nestjs/common';
import { AgentController } from './agent.controller';
import { AgentService } from './agent.service';
import { ToolsModule } from '../tools/tools.module';
import { AiModule } from '../ai/ai.module';

@Module({
  imports: [ToolsModule, AiModule],
  controllers: [AgentController],
  providers: [AgentService],
})
export class AgentModule {}
