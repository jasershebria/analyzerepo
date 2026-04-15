import { Component } from '@angular/core';
import { RecentAnalysis, StatCard } from '../../models/analysis.models';

@Component({
  selector: 'app-dashboard',
  standalone: false,
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent {
  stats: StatCard[] = [
    {
      label: 'Repositories Analyzed',
      value: '24',
      iconName: 'git-branch',
      change: '+12%',
      gradientFrom: '#6366F1',
      gradientTo: '#7C3AED',
    },
    {
      label: 'Total Flowcharts',
      value: '156',
      iconName: 'activity',
      change: '+23%',
      gradientFrom: '#10B981',
      gradientTo: '#059669',
    },
    {
      label: 'Hours Saved',
      value: '48',
      iconName: 'clock',
      change: '+18%',
      gradientFrom: '#F59E0B',
      gradientTo: '#D97706',
    },
    {
      label: 'This Month',
      value: '8',
      iconName: 'trending-up',
      change: '+5%',
      gradientFrom: '#EC4899',
      gradientTo: '#DB2777',
    },
  ];

  recentAnalyses: RecentAnalysis[] = [
    { name: 'E-commerce Platform', repo: 'github.com/acme/shop', date: '2 hours ago', flows: 12 },
    { name: 'Auth Service', repo: 'github.com/acme/auth', date: '1 day ago', flows: 8 },
    { name: 'Payment Gateway', repo: 'github.com/acme/payments', date: '3 days ago', flows: 15 },
  ];

  getGradient(from: string, to: string): string {
    return `linear-gradient(135deg, ${from}, ${to})`;
  }
}
