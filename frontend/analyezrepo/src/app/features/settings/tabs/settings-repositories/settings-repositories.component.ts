import { Component, inject, signal, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { RepositoryDto } from '../../../../models/analysis.models';
import { RepositoryService } from './services/repository.service';

@Component({
  selector: 'app-settings-repositories',
  standalone: false,
  templateUrl: './settings-repositories.component.html',
  styleUrl: './settings-repositories.component.scss',
})
export class SettingsRepositoriesComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly repositoryService = inject(RepositoryService);

  readonly repositories = signal<RepositoryDto[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.loadRepositories();
  }

  navigateToAddRepo(): void {
    this.router.navigate(['/settings/repositories/add']);
  }

  deleteRepo(id: string): void {
    this.repositoryService.delete(id).subscribe({
      next: () => this.repositories.update(repos => repos.filter(r => r.id !== id)),
      error: () => this.error.set('Failed to delete repository.'),
    });
  }

  private loadRepositories(): void {
    this.loading.set(true);
    this.repositoryService.getAll().subscribe({
      next: result => {
        this.repositories.set(result.items);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load repositories.');
        this.loading.set(false);
      },
    });
  }
}
