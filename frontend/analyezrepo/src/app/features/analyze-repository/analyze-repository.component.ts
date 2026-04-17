import { Component, inject, signal } from '@angular/core';
import { Repository } from '../../models/analysis.models';
import { AnalysisStateService } from './services/analysis-state.service';

@Component({
  selector: 'app-analyze-repository',
  standalone: false,
  templateUrl: './analyze-repository.component.html',
  styleUrl: './analyze-repository.component.scss',
})
export class AnalyzeRepositoryComponent {
  private readonly state = inject(AnalysisStateService);

  readonly selectedRepo = signal<Repository | null>(null);

  selectRepo(repo: Repository): void {
    this.selectedRepo.set(repo);
    this.state.connect(repo);
  }

  deselectRepo(): void {
    this.selectedRepo.set(null);
    this.state.reset();
  }
}
