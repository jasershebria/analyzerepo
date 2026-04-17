import { Component, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Repository } from '../../../../../models/analysis.models';

@Component({
  selector: 'app-add-repository',
  standalone: false,
  templateUrl: './add-repository.component.html',
  styleUrl: './add-repository.component.scss',
})
export class AddRepositoryComponent {
  private readonly router = inject(Router);

  readonly name = signal('');
  readonly repoUrl = signal('');
  readonly token = signal('');
  readonly isSubmitting = signal(false);

  readonly canSubmit = computed(
    () => !!this.repoUrl().trim() && !!this.token().trim() && !this.isSubmitting()
  );

  handleSubmit(): void {
    if (!this.canSubmit()) return;
    this.isSubmitting.set(true);

    const url = this.repoUrl().trim();
    const existing: Repository[] = JSON.parse(localStorage.getItem('repositories') ?? '[]');
    const newRepo: Repository = {
      id: Date.now().toString(),
      name: this.name().trim() || url.split('/').pop() || 'Unnamed Repository',
      url,
      token: this.token().trim(),
      addedAt: new Date().toISOString(),
    };

    localStorage.setItem('repositories', JSON.stringify([...existing, newRepo]));

    setTimeout(() => {
      this.isSubmitting.set(false);
      this.router.navigate(['/settings/repositories']);
    }, 500);
  }

  goBack(): void {
    this.router.navigate(['/settings/repositories']);
  }
}
