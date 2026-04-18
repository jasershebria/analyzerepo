import { Component, inject, signal, OnInit } from '@angular/core';
import { ProviderDto } from '../../../../models/analysis.models';
import { ProviderService } from '../settings-repositories/services/provider.service';

@Component({
  selector: 'app-settings-providers',
  standalone: false,
  templateUrl: './settings-providers.component.html',
  styleUrl: './settings-providers.component.scss',
})
export class SettingsProvidersComponent implements OnInit {
  private readonly providerService = inject(ProviderService);

  readonly providers = signal<ProviderDto[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly showModal = signal(false);

  ngOnInit(): void {
    this.loadProviders();
  }

  openAddModal(): void {
    this.showModal.set(true);
  }

  onModalSaved(provider: ProviderDto): void {
    this.providers.update(list => [...list, provider]);
    this.showModal.set(false);
  }

  onModalCancelled(): void {
    this.showModal.set(false);
  }

  deleteProvider(id: string): void {
    this.providerService.delete(id).subscribe({
      next: () => this.providers.update(list => list.filter(p => p.id !== id)),
      error: () => this.error.set('Failed to delete provider.'),
    });
  }

  private loadProviders(): void {
    this.loading.set(true);
    this.providerService.getAll().subscribe({
      next: result => {
        this.providers.set(result.items as ProviderDto[]);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load providers.');
        this.loading.set(false);
      },
    });
  }
}
