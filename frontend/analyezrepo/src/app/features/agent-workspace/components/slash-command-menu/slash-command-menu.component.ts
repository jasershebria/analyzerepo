import { Component, EventEmitter, Input, Output, ChangeDetectionStrategy } from '@angular/core';
import { Skill } from '../../services/skills.service';

@Component({
  selector: 'app-slash-command-menu',
  templateUrl: './slash-command-menu.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class SlashCommandMenuComponent {
  @Input({ required: true }) skills!: Skill[];
  @Input() filter = '';
  @Output() selected = new EventEmitter<Skill>();

  get filtered(): Skill[] {
    const q = this.filter.toLowerCase();
    return this.skills.filter(s => s.name.includes(q) || s.description.toLowerCase().includes(q));
  }

  select(skill: Skill): void {
    this.selected.emit(skill);
  }
}
