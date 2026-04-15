import { Component, Input } from '@angular/core';
import {
  animate,
  state,
  style,
  transition,
  trigger,
} from '@angular/animations';
import { AnalysisStep } from '../../../../../models/analysis.models';

@Component({
  selector: 'app-flow-explanation',
  standalone: false,
  templateUrl: './flow-explanation.component.html',
  styleUrl: './flow-explanation.component.scss',
  animations: [
    trigger('expandCollapse', [
      state('collapsed', style({ height: '0', opacity: '0', overflow: 'hidden' })),
      state('expanded', style({ height: '*', opacity: '1', overflow: 'hidden' })),
      transition('collapsed <=> expanded', [animate('200ms ease')]),
    ]),
  ],
})
export class FlowExplanationComponent {
  @Input() steps: AnalysisStep[] = [];
  expandedStep: number | null = null;

  toggle(stepNumber: number): void {
    this.expandedStep = this.expandedStep === stepNumber ? null : stepNumber;
  }

  isExpanded(stepNumber: number): boolean {
    return this.expandedStep === stepNumber;
  }

  getGradient(from: string, to: string): string {
    return `linear-gradient(135deg, ${from}, ${to})`;
  }
}
