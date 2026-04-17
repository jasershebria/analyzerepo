import { Component, signal } from '@angular/core';

interface NotificationOption {
  label: string;
  checked: boolean;
}

@Component({
  selector: 'app-settings-notifications',
  standalone: false,
  templateUrl: './settings-notifications.component.html',
  styleUrl: './settings-notifications.component.scss',
})
export class SettingsNotificationsComponent {
  readonly notificationOptions = signal<NotificationOption[]>([
    { label: 'Analysis complete notifications', checked: true },
    { label: 'Weekly usage reports',            checked: true },
    { label: 'New feature announcements',       checked: false },
  ]);

  toggleOption(index: number): void {
    this.notificationOptions.update(opts =>
      opts.map((opt, i) => i === index ? { ...opt, checked: !opt.checked } : opt)
    );
  }

  saveChanges(): void {
    console.log('Notification settings saved', this.notificationOptions());
  }
}
