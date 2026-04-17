import { Component, inject, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { FormBuilder, FormArray, Validators } from '@angular/forms';
import { RepositoryService } from '../../services/repository.service';
import { ProviderService } from '../../services/provider.service';
import { ProviderDto } from '../../../../../../models/analysis.models';

@Component({
  selector: 'app-add-repository',
  standalone: false,
  templateUrl: './add-repository.component.html',
  styleUrl: './add-repository.component.scss',
})
export class AddRepositoryComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly repositoryService = inject(RepositoryService);
  private readonly providerService = inject(ProviderService);

  isSubmitting = false;
  errorMessage = '';
  providers: ProviderDto[] = [];

  readonly authTypes = [
    { value: 1, label: 'Personal Access Token' },
    { value: 2, label: 'OAuth' },
    { value: 3, label: 'App Installation' },
  ];

  form = this.fb.group({
    name: ['', [Validators.required, Validators.maxLength(200)]],
    providerId: ['', [Validators.required]],
    webUrl: ['', [Validators.required, Validators.maxLength(500)]],
    authenticationType: [1, [Validators.required]],
    secretRef: ['', [Validators.required, Validators.maxLength(500)]],
    branchRules: this.fb.array([
      this.fb.group({
        pattern: ['main', [Validators.required, Validators.maxLength(200)]],
        scanOnPush: [true],
      }),
    ]),
  });

  ngOnInit(): void {
    this.providerService.getAll().subscribe({
      next: (result) => (this.providers = result.items as ProviderDto[]),
      error: () => (this.errorMessage = 'Failed to load providers.'),
    });
  }

  get branchRules(): FormArray {
    return this.form.get('branchRules') as FormArray;
  }

  addBranchRule(): void {
    this.branchRules.push(
      this.fb.group({
        pattern: ['', [Validators.required, Validators.maxLength(200)]],
        scanOnPush: [true],
      })
    );
  }

  removeBranchRule(index: number): void {
    if (this.branchRules.length > 1) {
      this.branchRules.removeAt(index);
    }
  }

  handleSubmit(): void {
    if (this.form.invalid || this.isSubmitting) return;
    this.isSubmitting = true;
    this.errorMessage = '';

    const v = this.form.getRawValue();
    const webUrl = v.webUrl!.trim().replace(/\/$/, '');
    const urlPath = new URL(webUrl).pathname.replace(/^\//, '').replace(/\.git$/, '');

    this.repositoryService.create({
      providerId: v.providerId!,
      providerRepoId: urlPath,
      name: v.name!,
      webUrl,
      cloneUrl: webUrl.endsWith('.git') ? webUrl : `${webUrl}.git`,
      defaultBranch: 'main',
      authenticationType: v.authenticationType!,
      secretRef: v.secretRef!,
      runInitialScan: false,
      branchRules: v.branchRules!.map(r => ({ pattern: r.pattern!, scanOnPush: r.scanOnPush! })),
    }).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.router.navigate(['/settings/repositories']);
      },
      error: (err) => {
        this.isSubmitting = false;
        this.errorMessage = err?.error?.message ?? 'Failed to add repository.';
      },
    });
  }

  goBack(): void {
    this.router.navigate(['/settings/repositories']);
  }
}
