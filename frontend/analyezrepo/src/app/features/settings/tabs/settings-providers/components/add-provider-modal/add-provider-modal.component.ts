import { Component, EventEmitter, Output, inject } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { ProviderService } from '../../../settings-repositories/services/provider.service';
import { ProviderDto } from '../../../../../../models/analysis.models';

@Component({
  selector: 'app-add-provider-modal',
  standalone: false,
  templateUrl: './add-provider-modal.component.html',
  styleUrl: './add-provider-modal.component.scss',
})
export class AddProviderModalComponent {
  @Output() saved = new EventEmitter<ProviderDto>();
  @Output() cancelled = new EventEmitter<void>();

  private readonly fb = inject(FormBuilder);
  private readonly providerService = inject(ProviderService);

  isSubmitting = false;
  errorMessage = '';

  form = this.fb.group({
    name: ['', [Validators.required, Validators.maxLength(200)]],
    code: ['', [Validators.required, Validators.maxLength(50), Validators.pattern('^[a-z0-9_-]+$')]],
    apiBaseUrl: ['', [Validators.required, Validators.maxLength(500)]],
  });

  handleSubmit(): void {
    if (this.form.invalid || this.isSubmitting) return;
    this.isSubmitting = true;
    this.errorMessage = '';

    const v = this.form.getRawValue();

    this.providerService.create({
      name: v.name!,
      code: v.code!,
      apiBaseUrl: v.apiBaseUrl!,
    }).subscribe({
      next: (provider) => {
        this.isSubmitting = false;
        this.saved.emit(provider);
      },
      error: (err) => {
        this.isSubmitting = false;
        this.errorMessage = err?.error?.message ?? 'Failed to create provider.';
      },
    });
  }

  cancel(): void {
    this.cancelled.emit();
  }

  onBackdropClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-backdrop')) {
      this.cancel();
    }
  }
}
