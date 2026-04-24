import { Component } from '@angular/core';

interface NavItem {
  path: string;
  label: string;
  iconName: string;
  exact: boolean;
}

@Component({
  selector: 'app-sidebar',
  standalone: false,
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss',
})
export class SidebarComponent {
  navItems: NavItem[] = [
    { path: '/', label: 'Dashboard', iconName: 'layout-dashboard', exact: true },
    { path: '/analyze', label: 'Analyze Repository', iconName: 'git-branch', exact: false },
    { path: '/agent', label: 'AI Agent', iconName: 'sparkles', exact: false },
    { path: '/history', label: 'History', iconName: 'history', exact: false },
    { path: '/settings', label: 'Settings', iconName: 'settings', exact: false },
  ];
}
