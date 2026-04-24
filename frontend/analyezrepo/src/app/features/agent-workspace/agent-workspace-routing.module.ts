import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AgentChatComponent } from './components/agent-chat/agent-chat.component';

const routes: Routes = [
  { path: '', component: AgentChatComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AgentWorkspaceRoutingModule {}
