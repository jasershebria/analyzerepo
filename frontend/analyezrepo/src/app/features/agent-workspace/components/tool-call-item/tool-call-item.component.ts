import { Component, Input, signal, ChangeDetectionStrategy } from '@angular/core';
import { ToolCall } from '../../services/agent-state.service';

const DESTRUCTIVE_TOOLS = new Set(['file_write', 'file_edit', 'bash', 'powershell', 'git_commit']);

@Component({
  selector: 'app-tool-call-item',
  templateUrl: './tool-call-item.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class ToolCallItemComponent {
  @Input({ required: true }) toolCall!: ToolCall;

  readonly expanded = signal(false);

  get isDestructive(): boolean {
    return DESTRUCTIVE_TOOLS.has(this.toolCall.tool);
  }

  get inputSummary(): string {
    const input = this.toolCall.input;
    const first = Object.values(input)[0];
    if (typeof first === 'string') return first.slice(0, 60);
    return '';
  }

  toggle(): void {
    this.expanded.update(v => !v);
  }

  formatJson(obj: unknown): string {
    return JSON.stringify(obj, null, 2);
  }
}
