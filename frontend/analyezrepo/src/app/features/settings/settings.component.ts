import { Component } from '@angular/core';

@Component({
  selector: 'app-settings',
  standalone: false,
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss',
})
export class SettingsComponent {
  githubToken = '';
  selectedModel = 'GPT-4 Turbo';
  analysisDepth = 5;

  notificationOptions = [
    { label: 'Analysis complete notifications', checked: true },
    { label: 'Weekly usage reports', checked: true },
    { label: 'New feature announcements', checked: false },
  ];

  aiModels = ['GPT-4 Turbo', 'GPT-4', 'Claude 3 Opus', 'Claude Sonnet 4.6'];

  saveChanges(): void {
    // Would call an API in a real implementation
    console.log('Settings saved');
  }
}
