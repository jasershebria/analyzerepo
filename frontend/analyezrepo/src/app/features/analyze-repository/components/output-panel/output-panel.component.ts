import { Component, OnInit } from '@angular/core';
import { AnalysisStateService } from '../../services/analysis-state.service';
import { AnalysisData } from '../../../../models/analysis.models';

@Component({
  selector: 'app-output-panel',
  standalone: false,
  templateUrl: './output-panel.component.html',
  styleUrl: './output-panel.component.scss',
})
export class OutputPanelComponent implements OnInit {
  data: AnalysisData | null = null;
  activeTab: 'flow' | 'chart' | 'code' = 'flow';

  constructor(private analysisState: AnalysisStateService) {}

  ngOnInit(): void {
    this.analysisState.analysisData$.subscribe((d) => {
      this.data = d;
      if (d) this.activeTab = 'flow';
    });
  }

  setTab(tab: 'flow' | 'chart' | 'code'): void {
    this.activeTab = tab;
  }
}
