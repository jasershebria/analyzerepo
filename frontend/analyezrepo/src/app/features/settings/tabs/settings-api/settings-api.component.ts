import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-settings-api',
  standalone: false,
  templateUrl: './settings-api.component.html',
  styleUrl: './settings-api.component.scss',
})
export class SettingsApiComponent {
  readonly aiModels = ['GPT-4 Turbo', 'GPT-4', 'Claude 3 Opus', 'Claude Sonnet 4.6'];

  readonly selectedModel = signal('GPT-4 Turbo');
  readonly analysisDepth = signal(5);

  saveChanges(): void {
    console.log('API settings saved', this.selectedModel(), this.analysisDepth());
  }
}
