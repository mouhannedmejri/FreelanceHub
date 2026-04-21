import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { NotificationService } from '../../services/notification.service';
import { Notification } from '../../models/notification.model';
import { Subscription } from 'rxjs';

@Component({
    selector: 'app-notifications',
    templateUrl: './notifications.page.html',
    styleUrls: ['./notifications.page.scss'],
    standalone: false,
})
export class NotificationsPage implements OnInit, OnDestroy {
    notifications: Notification[] = [];
    filter: 'all' | 'unread' = 'all';
    loading = false;
    private sub!: Subscription;

    constructor(
        private notificationService: NotificationService,
        private router: Router
    ) { }

    ngOnInit() {
        this.sub = this.notificationService.notifications$.subscribe((n) => {
            this.notifications = n;
        });
        this.loadNotifications();
    }

    ngOnDestroy() {
        this.sub?.unsubscribe();
    }

    loadNotifications() {
        this.loading = true;
        this.notificationService.loadNotifications().subscribe({
            next: () => (this.loading = false),
            error: () => (this.loading = false),
        });
    }

    get totalCount(): number {
        return this.notifications.length;
    }

    get unreadCount(): number {
        return this.notifications.filter((n) => !n.is_read).length;
    }

    get displayedNotifications(): Notification[] {
        if (this.filter === 'unread') {
            return this.notifications.filter((n) => !n.is_read);
        }
        return this.notifications;
    }

    setFilter(f: 'all' | 'unread') {
        this.filter = f;
    }

    markAsRead(notif: Notification) {
        if (notif.is_read) return;
        this.notificationService.markAsRead(notif.id).subscribe();
    }

    markAllAsRead() {
        this.notificationService.markAllAsRead().subscribe();
    }

    deleteNotification(notif: Notification, event: Event) {
        event.stopPropagation();
        this.notificationService.deleteNotification(notif.id).subscribe();
    }

    getTypeIcon(type: string): string {
        switch (type) {
            case 'message': return 'chatbubble-outline';
            case 'offer': return 'briefcase-outline';
            case 'payment': return 'card-outline';
            case 'review': return 'star-outline';
            default: return 'notifications-outline';
        }
    }

    getTypeColor(type: string): string {
        switch (type) {
            case 'message': return '#818cf8'; // indigo
            case 'offer': return '#a78bfa'; // purple
            case 'payment': return '#34d399'; // emerald
            case 'review': return '#fbbf24'; // amber
            default: return '#a78bfa';
        }
    }

    formatTime(dateStr: string): string {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHrs = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'À l\'instant';
        if (diffMins < 60) return `il y a ${diffMins} min`;
        if (diffHrs < 24) return `il y a ${diffHrs}h`;
        if (diffDays < 7) return `il y a ${diffDays}j`;
        return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    }

    goBack() {
        this.router.navigate(['/home']);
    }
}
