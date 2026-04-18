import { Component, computed, inject, output, signal } from '@angular/core';
import { Router } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { catchError, map, of, startWith } from 'rxjs';
import { RepositoryDto } from '../../../../models/analysis.models';
import { RepositoryService } from '../../../settings/tabs/settings-repositories/services/repository.service';

@Component({
  selector: 'app-repository-input',
  standalone: false,
  templateUrl: './repository-input.component.html',
  styleUrl: './repository-input.component.scss',
})
export class RepositoryInputComponent {
  private readonly router = inject(Router);
  private readonly repositoryService = inject(RepositoryService);

  readonly repoSelected = output<RepositoryDto>();

  private readonly result = toSignal(
    this.repositoryService.getAll().pipe(
      map(res => ({ items: res.items, loading: false, error: false })),
      startWith({ items: [] as RepositoryDto[], loading: true, error: false }),
      catchError(() => of({ items: [] as RepositoryDto[], loading: false, error: true }))
    ),
    { initialValue: { items: [] as RepositoryDto[], loading: true, error: false } }
  );

  readonly repositories = computed(() => this.result().items);
  readonly loading = computed(() => this.result().loading);
  readonly error = computed(() => this.result().error);

  selectRepo(repo: RepositoryDto): void {
    this.repoSelected.emit(repo);
  }

  navigateToAddRepo(): void {
    this.router.navigate(['/settings']);
  }
}
