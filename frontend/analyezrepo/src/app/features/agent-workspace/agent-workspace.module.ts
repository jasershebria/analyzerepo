import { NgModule } from '@angular/core';
import { SharedModule } from '../../shared/shared.module';
import { AgentWorkspaceRoutingModule } from './agent-workspace-routing.module';
import { AgentChatComponent } from './components/agent-chat/agent-chat.component';
import { ToolCallItemComponent } from './components/tool-call-item/tool-call-item.component';
import { PlanDisplayComponent } from './components/plan-display/plan-display.component';
import { SlashCommandMenuComponent } from './components/slash-command-menu/slash-command-menu.component';
import { AgentStateService } from './services/agent-state.service';

@NgModule({
  declarations: [
    AgentChatComponent,
    ToolCallItemComponent,
    PlanDisplayComponent,
    SlashCommandMenuComponent,
  ],
  imports: [SharedModule, AgentWorkspaceRoutingModule],
  exports: [AgentChatComponent],
  providers: [AgentStateService],
})
export class AgentWorkspaceModule {}
