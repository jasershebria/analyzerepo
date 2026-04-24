import { NgModule } from '@angular/core';
import { AnalyzeRepositoryRoutingModule } from './analyze-repository-routing.module';
import { AnalyzeRepositoryComponent } from './analyze-repository.component';
import { RepositoryInputComponent } from './components/repository-input/repository-input.component';
import { ChatInterfaceComponent } from './components/chat-interface/chat-interface.component';
import { OutputPanelComponent } from './components/output-panel/output-panel.component';
import { FlowExplanationComponent } from './components/output-panel/flow-explanation/flow-explanation.component';
import { FlowchartViewerComponent } from './components/output-panel/flowchart-viewer/flowchart-viewer.component';
import { CodeReferencesComponent } from './components/output-panel/code-references/code-references.component';
import { AnalysisStateService } from './services/analysis-state.service';
import { SharedModule } from '../../shared/shared.module';
import { RepoSessionComponent } from './components/repo-session/repo-session.component';
import { AgentWorkspaceModule } from '../agent-workspace/agent-workspace.module';

@NgModule({
  declarations: [
    AnalyzeRepositoryComponent,
    RepoSessionComponent,
    RepositoryInputComponent,
    ChatInterfaceComponent,
    OutputPanelComponent,
    FlowExplanationComponent,
    FlowchartViewerComponent,
    CodeReferencesComponent,
  ],
  imports: [SharedModule, AnalyzeRepositoryRoutingModule, AgentWorkspaceModule],
  providers: [AnalysisStateService],
})
export class AnalyzeRepositoryModule {}
