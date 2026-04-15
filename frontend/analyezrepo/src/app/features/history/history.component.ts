import { Component } from '@angular/core';
import { HistoryItem } from '../../models/analysis.models';

@Component({
  selector: 'app-history',
  standalone: false,
  templateUrl: './history.component.html',
  styleUrl: './history.component.scss',
})
export class HistoryComponent {
  searchQuery = '';

  allHistory: HistoryItem[] = [
    { id: 1, name: 'E-commerce Platform - Checkout Flow', repo: 'github.com/acme/shop', date: 'April 14, 2026', time: '2:30 PM', flows: 12, queries: 8 },
    { id: 2, name: 'Authentication Service Analysis', repo: 'github.com/acme/auth', date: 'April 13, 2026', time: '10:15 AM', flows: 8, queries: 5 },
    { id: 3, name: 'Payment Gateway Integration', repo: 'github.com/acme/payments', date: 'April 12, 2026', time: '4:45 PM', flows: 15, queries: 12 },
    { id: 4, name: 'Reservation System Flow', repo: 'github.com/acme/reservations', date: 'April 11, 2026', time: '11:20 AM', flows: 10, queries: 7 },
    { id: 5, name: 'Notification Service', repo: 'github.com/acme/notifications', date: 'April 10, 2026', time: '3:00 PM', flows: 6, queries: 4 },
  ];

  get filteredHistory(): HistoryItem[] {
    if (!this.searchQuery.trim()) return this.allHistory;
    const q = this.searchQuery.toLowerCase();
    return this.allHistory.filter(
      (item) =>
        item.name.toLowerCase().includes(q) ||
        item.repo.toLowerCase().includes(q)
    );
  }

  deleteItem(id: number): void {
    const idx = this.allHistory.findIndex((h) => h.id === id);
    if (idx !== -1) this.allHistory.splice(idx, 1);
  }
}
