import {
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  AfterViewChecked,
} from '@angular/core';
import {
  animate,
  style,
  transition,
  trigger,
} from '@angular/animations';
import { AnalysisStateService } from '../../services/analysis-state.service';
import { Message } from '../../../../models/analysis.models';

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
export class ChatInterfaceComponent implements OnInit, AfterViewChecked {
  @ViewChild('messagesEnd') messagesEndRef!: ElementRef;

  messages: Message[] = [];
  isConnected = false;
  inputText = '';
  private shouldScroll = false;

  exampleQuestions = [
    'How does the reservation flow work?',
    'Explain the authentication process',
    'How does payment processing work?',
  ];

  constructor(private analysisState: AnalysisStateService) {}

  ngOnInit(): void {
    this.analysisState.messages$.subscribe((msgs) => {
      this.messages = msgs;
      this.shouldScroll = true;
    });
    this.analysisState.isConnected$.subscribe(
      (connected) => (this.isConnected = connected)
    );
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  private scrollToBottom(): void {
    try {
      this.messagesEndRef.nativeElement.scrollIntoView({ behavior: 'smooth' });
    } catch (_) {}
  }

  sendMessage(text?: string): void {
    const msg = (text ?? this.inputText).trim();
    if (!msg || !this.isConnected) return;
    this.inputText = '';
    this.analysisState.sendMessage(msg);
  }

  handleKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  trackByIndex(index: number): number {
    return index;
  }
}
