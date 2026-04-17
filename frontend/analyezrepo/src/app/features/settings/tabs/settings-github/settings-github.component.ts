import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-settings-github',
  standalone: false,
  templateUrl: './settings-github.component.html',
  styleUrl: './settings-github.component.scss',
})
export class SettingsGithubComponent {
  readonly githubToken = signal('');

  saveChanges(): void {
    console.log('GitHub settings saved', this.githubToken());
  }
}
