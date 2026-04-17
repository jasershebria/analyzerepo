import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

export interface Repository {
  id: string;
  name: string;
  url: string;
  addedAt: string;
}

@Component({
  selector: 'app-settings-repositories',
  standalone: false,
  templateUrl: './settings-repositories.component.html',
  styleUrl: './settings-repositories.component.scss',
})
export class SettingsRepositoriesComponent {
  private readonly router = inject(Router);

  readonly repositories = signal<Repository[]>(
    JSON.parse(localStorage.getItem('repositories') ?? '[]')
  );

  deleteRepo(id: string): void {
    this.repositories.update(repos => repos.filter(r => r.id !== id));
    localStorage.setItem('repositories', JSON.stringify(this.repositories()));
  }

  navigateToAddRepo(): void {
    this.router.navigate(['/analyze']);
  }
}
