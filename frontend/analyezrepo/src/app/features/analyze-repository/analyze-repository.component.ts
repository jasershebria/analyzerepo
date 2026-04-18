import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { RepositoryDto } from '../../models/analysis.models';

@Component({
  selector: 'app-analyze-repository',
  standalone: false,
  templateUrl: './analyze-repository.component.html',
  styleUrl: './analyze-repository.component.scss',
})
export class AnalyzeRepositoryComponent {
  private readonly router = inject(Router);

  selectRepo(dto: RepositoryDto): void {
    this.router.navigate(['/analyze', dto.id]);
  }
}
