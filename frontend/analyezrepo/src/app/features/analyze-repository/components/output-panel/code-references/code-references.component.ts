import { Component, Input } from '@angular/core';
import {
  animate,
  state,
  style,
  transition,
  trigger,
} from '@angular/animations';
import { CodeReference } from '../../../../../models/analysis.models';

@Component({
  selector: 'app-code-references',
  standalone: false,
  templateUrl: './code-references.component.html',
  styleUrl: './code-references.component.scss',
  animations: [
    trigger('expandCollapse', [
      state('collapsed', style({ height: '0', opacity: '0', overflow: 'hidden' })),
      state('expanded', style({ height: '*', opacity: '1', overflow: 'hidden' })),
      transition('collapsed <=> expanded', [animate('200ms ease')]),
    ]),
  ],
})
export class CodeReferencesComponent {
  @Input() references: CodeReference[] = [];

  expandedFile: string | null = null;
  copiedFile: string | null = null;

  toggle(file: string): void {
    this.expandedFile = this.expandedFile === file ? null : file;
  }

  isExpanded(file: string): boolean {
    return this.expandedFile === file;
  }

  copySnippet(event: Event, snippet: string, file: string): void {
    event.stopPropagation();
    navigator.clipboard.writeText(snippet).then(() => {
      this.copiedFile = file;
      setTimeout(() => (this.copiedFile = null), 2000);
    });
  }

  isCopied(file: string): boolean {
    return this.copiedFile === file;
  }
}
