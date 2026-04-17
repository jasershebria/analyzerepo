import { Component, signal } from '@angular/core';

export type TabType = 'repositories' | 'github' | 'api' | 'notifications' | 'appearance';

@Component({
  selector: 'app-settings',
  standalone: false,
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss',
})
export class SettingsComponent {
  readonly activeTab = signal<TabType>('repositories');

  readonly tabs: { id: TabType; label: string; icon: string }[] = [
    { id: 'repositories',  label: 'Repositories', icon: 'folder-git-2' },
    { id: 'github',        label: 'GitHub',        icon: 'github' },
    { id: 'api',           label: 'API Config',    icon: 'key' },
    { id: 'notifications', label: 'Notifications', icon: 'bell' },
    { id: 'appearance',    label: 'Appearance',    icon: 'palette' },
  ];

  setTab(tab: TabType): void {
    this.activeTab.set(tab);
  }
}
