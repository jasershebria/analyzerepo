import { Component, computed, effect, inject, signal } from '@angular/core';
import { AnalysisStateService } from '../../services/analysis-state.service';

@Component({
  selector: 'app-output-panel',
  standalone: false,
  templateUrl: './output-panel.component.html',
  styleUrl: './output-panel.component.scss',
})
export class OutputPanelComponent {
  private readonly state = inject(AnalysisStateService);

  readonly data = this.state.analysisData;
  readonly activeTab = signal<'flow' | 'chart' | 'code'>('flow');

  readonly steps = computed(() => this.data()?.steps ?? []);
  readonly mermaidCode = computed(() => this.data()?.mermaidCode ?? '');
  readonly codeReferences = computed(() => this.data()?.codeReferences ?? []);

  constructor() {
    effect(() => {
      if (this.data()) this.activeTab.set('flow');
    });
  }

  setTab(tab: 'flow' | 'chart' | 'code'): void {
    this.activeTab.set(tab);
  }
}
