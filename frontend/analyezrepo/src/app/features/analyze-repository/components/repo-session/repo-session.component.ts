import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { GetRepositoryResponse } from '../../../../models/analysis.models';
import { RepositoryService } from '../../../settings/tabs/settings-repositories/services/repository.service';
import { AnalysisStateService } from '../../services/analysis-state.service';

@Component({
  selector: 'app-repo-session',
  standalone: false,
  templateUrl: './repo-session.component.html',
  styleUrl: './repo-session.component.scss',
})
export class RepoSessionComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly repositoryService = inject(RepositoryService);
  private readonly state = inject(AnalysisStateService);

  readonly repo = signal<GetRepositoryResponse | null>(null);
  readonly loading = signal(true);
  readonly error = signal(false);

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.repositoryService.getById(id).subscribe({
      next: (full) => {
        this.repo.set(full);
        this.state.connect(full);
        this.loading.set(false);
      },
      error: () => {
        this.error.set(true);
        this.loading.set(false);
      },
    });
  }

  goBack(): void {
    this.state.reset();
    this.router.navigate(['/analyze']);
  }
}
