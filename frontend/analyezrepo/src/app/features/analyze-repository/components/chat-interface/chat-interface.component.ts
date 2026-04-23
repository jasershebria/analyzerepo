import {
  AfterViewChecked,
  Component,
  effect,
  ElementRef,
  inject,
  signal,
  ViewChild,
} from '@angular/core';
import { animate, style, transition, trigger } from '@angular/animations';
import { AnalysisStateService } from '../../services/analysis-state.service';

@Component({
  selector: 'app-chat-interface',
  standalone: false,
  templateUrl: './chat-interface.component.html',
  styleUrl: './chat-interface.component.scss',
  animations: [
    trigger('messageEnter', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('300ms ease', style({ opacity: 1, transform: 'translateY(0)' })),
      ]),
    ]),
  ],
})
export class ChatInterfaceComponent implements AfterViewChecked {
  @ViewChild('messagesContainer') messagesContainerRef!: ElementRef<HTMLElement>;

  private readonly state = inject(AnalysisStateService);

  readonly messages = this.state.messages;
  readonly isConnected = this.state.isConnected;
  readonly isTyping = this.state.isTyping;
  readonly isLoadingContext = this.state.isLoadingContext;
  readonly inputText = signal('');

  private shouldScroll = false;

  readonly exampleQuestions = [
    'How does the reservation flow work?',
    'Explain the authentication process',
    'How does payment processing work?',
  ];

  constructor() {
    effect(() => {
      this.messages();
      this.isTyping();
      this.shouldScroll = true;
    });
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  private scrollToBottom(): void {
    const el = this.messagesContainerRef?.nativeElement;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }

  sendMessage(text?: string): void {
    const msg = (text ?? this.inputText()).trim();
    if (!msg || !this.isConnected()) return;
    this.inputText.set('');
    this.state.sendMessage(msg);
  }

  handleKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }
}
