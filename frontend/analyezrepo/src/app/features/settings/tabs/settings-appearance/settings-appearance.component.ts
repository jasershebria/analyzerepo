import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-settings-appearance',
  standalone: false,
  templateUrl: './settings-appearance.component.html',
  styleUrl: './settings-appearance.component.scss',
})
export class SettingsAppearanceComponent {
  readonly activeTheme = signal<'dark' | 'light'>('dark');

  saveChanges(): void {
    console.log('Appearance settings saved', this.activeTheme());
  }
}
