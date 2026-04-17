import { Component, inject, output, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Repository } from '../../../../models/analysis.models';

@Component({
  selector: 'app-repository-input',
  standalone: false,
  templateUrl: './repository-input.component.html',
  styleUrl: './repository-input.component.scss',
})
export class RepositoryInputComponent {
  private readonly router = inject(Router);

  readonly repoSelected = output<Repository>();

  readonly repositories = signal<Repository[]>(
    JSON.parse(localStorage.getItem('repositories') ?? '[]')
  );

  selectRepo(repo: Repository): void {
    this.repoSelected.emit(repo);
  }

  navigateToSettings(): void {
    this.router.navigate(['/settings']);
  }
}
