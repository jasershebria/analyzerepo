import {
  Component, OnInit, OnDestroy, ViewChild, ElementRef,
  ChangeDetectionStrategy, inject, signal, effect,
} from '@angular/core';
import { Subscription } from 'rxjs';
import { AgentStateService } from '../../services/agent-state.service';
import { SkillsService, Skill } from '../../services/skills.service';

@Component({
  selector: 'app-agent-chat',
  templateUrl: './agent-chat.component.html',
  styleUrl: './agent-chat.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class AgentChatComponent implements OnInit, OnDestroy {
  @ViewChild('messagesEnd') private messagesEnd!: ElementRef<HTMLDivElement>;
  @ViewChild('input') private inputRef!: ElementRef<HTMLTextAreaElement>;

  readonly state = inject(AgentStateService);
  private readonly skillsSvc = inject(SkillsService);

  readonly inputText = signal('');
  readonly skills = signal<Skill[]>([]);
  readonly showSlashMenu = signal(false);
  readonly slashFilter = signal('');

  private sub?: Subscription;

  constructor() {
    // Auto-scroll when messages change
    effect(() => {
      this.state.messages();
      setTimeout(() => this.scrollToBottom(), 50);
    });
  }

  ngOnInit(): void {
    this.sub = this.skillsSvc.getSkills().subscribe(s => this.skills.set(s));
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }

  onInputChange(value: string): void {
    this.inputText.set(value);
    const slashMatch = value.match(/^\/(\w*)$/);
    if (slashMatch) {
      this.showSlashMenu.set(true);
      this.slashFilter.set(slashMatch[1]);
    } else {
      this.showSlashMenu.set(false);
    }
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
    if (event.key === 'Escape') {
      this.showSlashMenu.set(false);
    }
  }

  selectSkill(skill: Skill): void {
    this.inputText.set(skill.prompt);
    this.showSlashMenu.set(false);
    this.inputRef?.nativeElement.focus();
  }

  send(): void {
    const text = this.inputText().trim();
    if (!text || this.state.isStreaming()) return;
    this.inputText.set('');
    this.showSlashMenu.set(false);
    this.state.sendMessage(text);
  }

  clear(): void {
    this.state.clearMessages();
  }

  private scrollToBottom(): void {
    this.messagesEnd?.nativeElement.scrollIntoView({ behavior: 'smooth' });
  }

  trackById(_: number, msg: { id: string }): string {
    return msg.id;
  }
}
