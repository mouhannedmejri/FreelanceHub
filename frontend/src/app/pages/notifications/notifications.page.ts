import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { NotificationService } from '../../services/notification.service';
import { Notification } from '../../models/notification.model';
import { Subscription } from 'rxjs';
import { ToastController } from '@ionic/angular';

interface NotificationGroup {
    label: string;
    notifications: Notification[];
}

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
        private toastController: ToastController,
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

    doRefresh(event: any) {
        this.notificationService.loadNotifications().subscribe({
            next: () => event.target.complete(),
            error: () => event.target.complete(),
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

    // ── GROUP BY DATE ────────────────────────
    get groupedNotifications(): NotificationGroup[] {
        const displayed = this.displayedNotifications;
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        const groups: { [key: string]: Notification[] } = {
            "Aujourd'hui": [],
            'Hier': [],
            'Plus ancien': []
        };

        for (const notif of displayed) {
            const date = new Date(notif.created_at);
            if (this.isSameDay(date, today)) {
                groups["Aujourd'hui"].push(notif);
            } else if (this.isSameDay(date, yesterday)) {
                groups['Hier'].push(notif);
            } else {
                groups['Plus ancien'].push(notif);
            }
        }

        return Object.entries(groups)
            .filter(([_, items]) => items.length > 0)
            .map(([label, notifications]) => ({ label, notifications }));
    }

    private isSameDay(d1: Date, d2: Date): boolean {
        return d1.getFullYear() === d2.getFullYear() &&
            d1.getMonth() === d2.getMonth() &&
            d1.getDate() === d2.getDate();
    }

    setFilter(f: 'all' | 'unread') {
        this.filter = f;
    }

    // ── SWIPE ACTIONS ────────────────────────
    markAsRead(notif: Notification) {
        if (notif.is_read) return;
        this.notificationService.markAsRead(notif.id).subscribe({
            next: () => {
                this.showToast('Marquée comme lue', 'checkmark-circle-outline');
            }
        });
    }

    markAllAsRead() {
        this.notificationService.markAllAsRead().subscribe({
            next: () => {
                this.showToast('Toutes les notifications marquées comme lues', 'checkmark-done-outline');
            }
        });
    }

    deleteNotification(notif: Notification) {
        this.notificationService.deleteNotification(notif.id).subscribe({
            next: () => {
                this.showToast('Notification supprimée', 'trash-outline');
            }
        });
    }

    // ── NOTIFICATION TYPE ICONS ──────────────
    getTypeIcon(type: string): string {
        switch (type) {
            case 'proposal_received': return 'paper-plane-outline';
            case 'proposal_accepted': return 'checkmark-circle-outline';
            case 'message': return 'chatbubble-outline';
            case 'milestone_due': return 'flag-outline';
            case 'review_received': return 'star-outline';
            case 'payment_released': return 'wallet-outline';
            case 'offer_approved': return 'shield-checkmark-outline';
            case 'offer': return 'briefcase-outline';
            case 'payment': return 'card-outline';
            case 'review': return 'star-outline';
            default: return 'notifications-outline';
        }
    }

    getTypeColor(type: string): string {
        switch (type) {
            case 'proposal_received': return '#a78bfa';
            case 'proposal_accepted': return '#34d399';
            case 'message': return '#60a5fa';
            case 'milestone_due': return '#f59e0b';
            case 'review_received': return '#fbbf24';
            case 'payment_released': return '#10b981';
            case 'offer_approved': return '#34d399';
            case 'offer': return '#a78bfa';
            case 'payment': return '#34d399';
            case 'review': return '#fbbf24';
            default: return '#a78bfa';
        }
    }

    getTypeBgColor(type: string): string {
        const color = this.getTypeColor(type);
        return color.replace(')', ', 0.12)').replace('rgb', 'rgba').replace('#', '');
        // Simpler approach:
    }

    getTypeBg(type: string): string {
        switch (type) {
            case 'proposal_received': return 'rgba(167,139,250,0.12)';
            case 'proposal_accepted': return 'rgba(52,211,153,0.12)';
            case 'message': return 'rgba(96,165,250,0.12)';
            case 'milestone_due': return 'rgba(245,158,11,0.12)';
            case 'review_received':
            case 'review': return 'rgba(251,191,36,0.12)';
            case 'payment_released':
            case 'payment': return 'rgba(16,185,129,0.12)';
            case 'offer_approved':
            case 'offer': return 'rgba(52,211,153,0.12)';
            default: return 'rgba(167,139,250,0.12)';
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

    private async showToast(message: string, icon: string) {
        const toast = await this.toastController.create({
            message,
            duration: 2000,
            position: 'bottom',
            icon,
            color: 'dark'
        });
        await toast.present();
    }
}
