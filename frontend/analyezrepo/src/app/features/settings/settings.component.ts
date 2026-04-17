import { Component } from '@angular/core';

@Component({
  selector: 'app-settings',
  standalone: false,
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss',
})
export class SettingsComponent {
  readonly tabs: { path: string; label: string; icon: string }[] = [
    { path: 'repositories',  label: 'Repositories', icon: 'folder-git-2' },
    { path: 'github',        label: 'GitHub',        icon: 'github' },
    { path: 'api',           label: 'API Config',    icon: 'key' },
    { path: 'notifications', label: 'Notifications', icon: 'bell' },
    { path: 'appearance',    label: 'Appearance',    icon: 'palette' },
  ];
}
