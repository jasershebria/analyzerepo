import { Component, inject, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { FormBuilder, FormArray, Validators } from '@angular/forms';
import { RepositoryService } from '../../services/repository.service';
import { ProviderService } from '../../services/provider.service';
import { ProviderDto, TestConnectionResponse } from '../../../../../../models/analysis.models';

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

  connectionStatus: 'idle' | 'testing' | 'success' | 'error' = 'idle';
  connectionError = '';
  connectionResult: TestConnectionResponse | null = null;
  branches: string[] = [];

  private readonly authTypeStrMap: Record<number, string> = {
    1: 'token',
    2: 'oauth',
    3: 'app',
  };

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
        pattern: [{ value: '', disabled: true }, [Validators.required, Validators.maxLength(200)]],
        scanOnPush: [true],
      }),
    ]),
  });

  ngOnInit(): void {
    this.providerService.getAll().subscribe({
      next: (result) => (this.providers = result.items as ProviderDto[]),
      error: () => (this.errorMessage = 'Failed to load providers.'),
    });

    // Reset connection when auth fields change
    const authFields = ['providerId', 'webUrl', 'authenticationType', 'secretRef'];
    authFields.forEach(field => {
      this.form.get(field)!.valueChanges.subscribe(() => {
        if (this.connectionStatus !== 'idle') {
          this.connectionStatus = 'idle';
          this.connectionResult = null;
          this.branches = [];
          this.branchRules.controls.forEach(c => {
            c.get('pattern')!.disable();
            c.patchValue({ pattern: '' });
          });
        }
      });
    });
  }

  get branchRules(): FormArray {
    return this.form.get('branchRules') as FormArray;
  }

  get canTestConnection(): boolean {
    const v = this.form.getRawValue();
    return !!(v.providerId && v.webUrl && v.secretRef) && this.connectionStatus !== 'testing';
  }

  testConnection(): void {
    if (!this.canTestConnection) return;
    this.connectionStatus = 'testing';
    this.connectionError = '';

    const v = this.form.getRawValue();
    const webUrl = v.webUrl!.trim().replace(/\/$/, '');

    this.repositoryService.testConnection({
      providerId: v.providerId!,
      webUrl,
      authType: this.authTypeStrMap[v.authenticationType as number] ?? 'token',
      secretRefOrToken: v.secretRef!,
    }).subscribe({
      next: (result) => {
        if (result.success) {
          this.connectionStatus = 'success';
          this.connectionResult = result;
          this.branches = result.branches.map(b => b.name);
          this.branchRules.controls.forEach(c => c.get('pattern')!.enable());
          if (result.defaultBranch && this.branchRules.length > 0) {
            this.branchRules.at(0).patchValue({ pattern: result.defaultBranch });
          }
        } else {
          this.connectionStatus = 'error';
          this.connectionError = result.errorMessage ?? 'Connection failed.';
          this.connectionResult = null;
          this.branches = [];
          this.branchRules.controls.forEach(c => {
            c.get('pattern')!.disable();
            c.patchValue({ pattern: '' });
          });
        }
      },
      error: (err) => {
        this.connectionStatus = 'error';
        this.connectionError = err?.error?.message ?? 'Connection failed.';
        this.connectionResult = null;
        this.branches = [];
        this.branchRules.controls.forEach(c => {
          c.get('pattern')!.disable();
          c.patchValue({ pattern: '' });
        });
      },
    });
  }

  addBranchRule(): void {
    const hasBranches = this.branches.length > 0;
    this.branchRules.push(
      this.fb.group({
        pattern: [
          { value: hasBranches ? this.branches[0] : '', disabled: !hasBranches },
          [Validators.required, Validators.maxLength(200)],
        ],
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
      providerRepoId: this.connectionResult?.providerRepoId ?? urlPath,
      name: v.name!,
      webUrl: this.connectionResult?.webUrlNormalized ?? webUrl,
      cloneUrl: this.connectionResult?.cloneUrl ?? `${webUrl}.git`,
      defaultBranch: this.connectionResult?.defaultBranch ?? 'main',
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
