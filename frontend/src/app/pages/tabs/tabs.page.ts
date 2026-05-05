import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { NotificationService } from '../../services/notification.service';
import { ConversationService } from '../../services/conversation.service';
import { User } from '../../models/user.model';
import { Subscription } from 'rxjs';
import { GuestAccessService } from '../../services/guest-access.service';

@Component({
  selector: 'app-tabs',
  templateUrl: './tabs.page.html',
  styleUrls: ['./tabs.page.scss'],
  standalone: false,
})
export class TabsPage implements OnInit, OnDestroy {
  user: User | null = null;
  unreadCount = 0;
  unreadMessagesCount = 0;
  activeProjectCount = 0;
  drawerOpen = false;
  private subs: Subscription[] = [];

  constructor(
    private authService: AuthService,
    private notificationService: NotificationService,
    private conversationService: ConversationService,
    private guestAccessService: GuestAccessService,
    private router: Router
  ) {}

  ngOnInit() {
    this.subs.push(
      this.authService.currentUser$.subscribe((user) => {
        this.user = user;
      })
    );

    this.subs.push(
      this.notificationService.unreadCount$.subscribe((count) => {
        this.unreadCount = count;
      })
    );

    this.subs.push(
      this.conversationService.unreadCount$.subscribe((count) => {
        this.unreadMessagesCount = count;
      })
    );

    if (this.authService.isAuthenticated) {
      this.notificationService.loadNotifications().subscribe();
      this.conversationService.getConversations().subscribe();
    }
  }

  ngOnDestroy() {
    this.subs.forEach((s) => s.unsubscribe());
  }

  get userInitials(): string {
    if (!this.user?.full_name) return '?';
    const parts = this.user.full_name.split(' ');
    return parts
      .map((p) => p[0])
      .join('')
      .toUpperCase()
      .substring(0, 2);
  }

  get roleLabel(): string {
    switch (this.user?.role) {
      case 'freelancer':
        return 'Freelancer';
      case 'client':
        return 'Client';
      case 'admin':
        return 'Administrateur';
      default:
        return '';
    }
  }

  get lastTabLabel(): string {
    return this.user?.role === 'client' ? 'Offres' : 'Profil';
  }

  get lastTabIcon(): string {
    return this.user?.role === 'client' ? 'document-text-outline' : 'person-outline';
  }

  toggleDrawer() {
    this.drawerOpen = !this.drawerOpen;
  }

  closeDrawer() {
    this.drawerOpen = false;
  }

  async openNotifications() {
    if (!this.authService.isAuthenticated) {
      const authed = await this.guestAccessService.showAuthModal(
        'Sign in to view notifications',
        { type: 'view_notifications', route: '/notifications' }
      );
      if (authed) this.router.navigate(['/notifications']);
      return;
    }
    this.router.navigate(['/notifications']);
  }

  navigateFromDrawer(route: string) {
    this.drawerOpen = false;
    this.router.navigate([route]);
  }

  async logout() {
    this.drawerOpen = false;
    if (this.authService.isGuest) {
      this.authService.exitGuestMode();
      this.router.navigate(['/auth'], { replaceUrl: true });
      return;
    }
    await this.authService.logout();
    this.router.navigate(['/auth'], { replaceUrl: true });
  }

  async openDashboard() {
    if (!this.user || !this.authService.isAuthenticated) {
      const authed = await this.guestAccessService.showAuthModal(
        'Sign in to access your dashboard',
        { type: 'view_dashboard', route: '/home/dashboard' }
      );
      if (!authed) return;
      // Reload user after auth
      this.user = this.authService.currentUser;
    }
    if (this.user?.role === 'client') {
      this.navigateFromDrawer('/client-dashboard');
      return;
    }
    if (this.user?.role === 'freelancer') {
      this.navigateFromDrawer('/freelancer-dashboard');
      return;
    }
    if (this.user?.role === 'admin') {
      this.navigateFromDrawer('/admin-dashboard');
      return;
    }
    this.navigateFromDrawer('/home/dashboard');
  }

  get isGuest(): boolean {
    return this.authService.isGuest;
  }

  get canSeeMessages(): boolean {
    return this.authService.isAuthenticated;
  }

  async handleMessagesTab(ev: Event) {
    if (this.canSeeMessages) {
      return;
    }
    ev.preventDefault();
    await this.guestAccessService.showAuthModal(
      'Sign in to access messages',
      { type: 'view_messages', route: '/home/messages' }
    );
  }
}
