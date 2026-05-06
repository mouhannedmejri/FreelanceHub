import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { HomeService, HomeStats } from '../services/home.service';
import { ProjectService } from '../services/project.service';
import { ProfileService } from '../services/profile.service';
import { GuestAccessService } from '../services/guest-access.service';
import { User } from '../models/user.model';
import { UpcomingMilestone } from '../models/project.model';
import { Subscription } from 'rxjs';
import { RecommendationService } from '../services/recommendation.service';
import { ToastController } from '@ionic/angular';

@Component({
  selector: 'app-home',
  templateUrl: 'home.page.html',
  styleUrls: ['home.page.scss'],
  standalone: false,
})
export class HomePage implements OnInit, OnDestroy {
  user: User | null = null;
  stats: HomeStats | null = null;
  searchQuery = '';
  upcomingMilestones: UpcomingMilestone[] = [];
  followingFeed: any[] = [];
  recommendedFreelancers: any[] = [];
  recommendedOffers: any[] = [];
  private sub!: Subscription;

  constructor(
    private authService: AuthService,
    private homeService: HomeService,
    private projectService: ProjectService,
    private profileService: ProfileService,
    private recommendationService: RecommendationService,
    private guestAccessService: GuestAccessService,
    private router: Router,
    private toastController: ToastController
  ) {}

  ngOnInit() {
    this.sub = this.authService.currentUser$.subscribe((user) => {
      this.user = user;
      if (this.authService.isAuthenticated && user?.role === 'client') {
        this.recommendationService.getFreelancerRecommendations(8).subscribe({
          next: (res) => (this.recommendedFreelancers = res.data || []),
          error: () => (this.recommendedFreelancers = []),
        });
      }
      if (this.authService.isAuthenticated && user?.role === 'freelancer') {
        this.recommendationService.getOpportunityRecommendations(10).subscribe({
          next: (res) => (this.recommendedOffers = res.data || []),
          error: () => (this.recommendedOffers = []),
        });
      }
    });

    this.homeService.getStats().subscribe({
      next: (s) => (this.stats = s),
      error: () => (this.stats = { freelancers: 15000, projects: 50000, clients: 12000 }),
    });

    if (this.authService.isAuthenticated) {
      this.projectService.getUpcomingMilestones().subscribe({
        next: (res) => (this.upcomingMilestones = res.milestones),
        error: () => (this.upcomingMilestones = []),
      });

      this.profileService.getFollowingFeed(5).subscribe({
        next: (res) => (this.followingFeed = res.feed),
        error: () => (this.followingFeed = []),
      });
    }
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }

  get formattedFreelancers(): string {
    return this.stats ? this.formatNum(this.stats.freelancers) : '...';
  }

  get formattedProjects(): string {
    return this.stats ? this.formatNum(this.stats.projects) : '...';
  }

  get formattedClients(): string {
    return this.stats ? this.formatNum(this.stats.clients) : '...';
  }

  private formatNum(n: number): string {
    if (n >= 1000) return (n / 1000).toFixed(0) + 'k+';
    return n.toString();
  }

  get filteredJobs(): any[] {
    if (!this.searchQuery.trim()) return this.recommendedOffers;
    const q = this.searchQuery.toLowerCase();
    return this.recommendedOffers.filter(
      (j) =>
        (j.title || '').toLowerCase().includes(q) ||
        (j.skills || []).some((s: string) => s.toLowerCase().includes(q))
    );
  }

  navigateTo(path: string) {
    this.router.navigate([path]);
  }

  goToAuth(tab: 'login' | 'register') {
    this.router.navigate(['/auth'], { queryParams: { tab } });
  }

  goToProjectMilestone(projectId: string) {
    this.router.navigate(['/project-detail', projectId]);
  }

  goToFreelancerProfile(userId: string) {
    this.recommendationService.trackInteraction({
      item_id: userId,
      item_type: 'freelancer',
      recommendation_type: 'freelancers',
      action: 'click',
    }).subscribe({ error: () => {} });
    this.router.navigate(['/home/profile'], {
      queryParams: { userId },
    });
  }

  async showWhyRecommended(reason?: string) {
    const toast = await this.toastController.create({
      message: reason || 'Recommended based on your interests and recent activity.',
      duration: 2200,
      color: 'medium',
      position: 'top',
    });
    await toast.present();
  }

  dismissFreelancerRecommendation(item: any) {
    const id = String(item?.id || '');
    if (!id) return;
    this.recommendationService.notInterested(id, 'freelancer').subscribe({
      next: () => {
        this.recommendedFreelancers = this.recommendedFreelancers.filter((f) => String(f.id) !== id);
      },
      error: () => {},
    });
  }

  getFeedIcon(type: string): string {
    switch (type) {
      case 'project':
        return 'briefcase-outline';
      case 'service':
        return 'pricetag-outline';
      default:
        return 'pulse-outline';
    }
  }

  getFeedColor(type: string): string {
    switch (type) {
      case 'project':
        return '#7c3aed';
      case 'service':
        return '#10b981';
      default:
        return '#3b82f6';
    }
  }

  async handleApply(job: any) {
    if (!this.authService.isAuthenticated) {
      const authed = await this.guestAccessService.showAuthModal('Sign in to apply for this offer', {
        type: 'apply_to_offer',
        targetId: String(job.id),
        route: `/home/store`,
      });
      if (!authed) return;
    }

    this.recommendationService.trackInteraction({
      item_id: job.id,
      item_type: 'offer',
      recommendation_type: 'opportunities',
      action: 'click',
      score: job?.recommendation?.score,
      reason: job?.recommendation?.why_recommended,
    }).subscribe({ error: () => {} });

    this.router.navigate(['/home/store'], { queryParams: { applyOfferId: job.id } });
  }
}
