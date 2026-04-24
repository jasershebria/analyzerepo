import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { TodoItem } from '../../services/agent-stream.service';

@Component({
  selector: 'app-plan-display',
  templateUrl: './plan-display.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class PlanDisplayComponent {
  @Input({ required: true }) tasks!: TodoItem[];

  get completedCount(): number {
    return this.tasks.filter(t => t.status === 'completed').length;
  }
}
