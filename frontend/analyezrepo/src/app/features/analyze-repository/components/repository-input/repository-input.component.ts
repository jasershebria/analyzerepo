import { Component } from '@angular/core';
import { AnalysisStateService } from '../../services/analysis-state.service';

@Component({
  selector: 'app-repository-input',
  standalone: false,
  templateUrl: './repository-input.component.html',
  styleUrl: './repository-input.component.scss',
})
export class RepositoryInputComponent {
  repoUrl = '';
  token = '';
  isLoading = false;
  isConnected = false;

  constructor(private analysisState: AnalysisStateService) {
    this.analysisState.isConnected$.subscribe(
      (connected) => (this.isConnected = connected)
    );
  }

  handleConnect(): void {
    if (!this.repoUrl || !this.token || this.isConnected) return;
    this.isLoading = true;
    setTimeout(() => {
      this.analysisState.connect(this.repoUrl, this.token);
      this.isLoading = false;
    }, 1500);
  }

  get canConnect(): boolean {
    return !!this.repoUrl && !!this.token && !this.isConnected && !this.isLoading;
  }
}
