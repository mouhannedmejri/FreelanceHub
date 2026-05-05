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

export interface RecommendedJob {
  id: number;
  title: string;
  client: string;
  description: string;
  skills: string[];
  budget: string;
  duration: string;
  location: string;
  propositions: number;
}

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
  private sub!: Subscription;

  recommendedJobs: RecommendedJob[] = [
    {
      id: 1,
      title: 'Développement Application Mobile React Native',
      client: 'TechStartup SAS',
      description:
        'Nous recherchons un développeur React Native expérimenté pour créer une application mobile cross-platform pour notre plateforme e-commerce.',
      skills: ['React Native', 'TypeScript', 'Redux', 'REST API'],
      budget: '2 500 – 4 000 €',
      duration: '2 mois',
      location: 'Remote',
      propositions: 7,
    },
    {
      id: 2,
      title: 'Refonte UI/UX Site E-commerce',
      client: 'ModeShop France',
      description:
        'Refonte complète de l\'interface utilisateur de notre boutique en ligne. Amélioration de l\'expérience d\'achat et du tunnel de conversion.',
      skills: ['Figma', 'UI Design', 'UX Research', 'Prototypage'],
      budget: '1 800 – 3 000 €',
      duration: '6 semaines',
      location: 'Paris ou Remote',
      propositions: 12,
    },
    {
      id: 3,
      title: 'Stratégie SEO & Content Marketing',
      client: 'AgenceGrowth',
      description:
        'Mission de conseil et exécution SEO pour booster la visibilité organique de nos clients. Audit, stratégie de contenu, netlinking.',
      skills: ['SEO', 'Content Marketing', 'Google Analytics', 'Ahrefs'],
      budget: '1 200 – 2 000 €',
      duration: '3 mois',
      location: 'Lyon ou Remote',
      propositions: 4,
    },
  ];

  constructor(
    private authService: AuthService,
    private homeService: HomeService,
    private projectService: ProjectService,
    private profileService: ProfileService,
    private guestAccessService: GuestAccessService,
    private router: Router
  ) { }

  ngOnInit() {
    this.sub = this.authService.currentUser$.subscribe((user) => {
      this.user = user;
    });

    this.homeService.getStats().subscribe({
      next: (s) => (this.stats = s),
      error: () =>
        (this.stats = { freelancers: 15000, projects: 50000, clients: 12000 }),
    });

    // Load upcoming milestones if authenticated
    if (this.authService.isAuthenticated) {
      this.projectService.getUpcomingMilestones().subscribe({
        next: (res) => (this.upcomingMilestones = res.milestones),
        error: () => (this.upcomingMilestones = []),
      });

      // Load following feed
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

  get filteredJobs(): RecommendedJob[] {
    if (!this.searchQuery.trim()) return this.recommendedJobs;
    const q = this.searchQuery.toLowerCase();
    return this.recommendedJobs.filter(
      (j) =>
        j.title.toLowerCase().includes(q) ||
        j.skills.some((s) => s.toLowerCase().includes(q))
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
    this.router.navigate(['/home/profile'], {
      queryParams: { userId }
    });
  }

  getFeedIcon(type: string): string {
    switch (type) {
      case 'project': return 'briefcase-outline';
      case 'service': return 'pricetag-outline';
      default: return 'pulse-outline';
    }
  }

  getFeedColor(type: string): string {
    switch (type) {
      case 'project': return '#7c3aed';
      case 'service': return '#10b981';
      default: return '#3b82f6';
    }
  }

  async handleApply(job: RecommendedJob) {
    if (!this.authService.isAuthenticated) {
      const authed = await this.guestAccessService.showAuthModal(
        'Sign in to apply for this offer',
        {
          type: 'apply_to_offer',
          targetId: String(job.id),
          route: `/project-detail/${job.id}`,
        }
      );
      if (!authed) return;
    }
    // Navigate to project detail or trigger proposal flow
    this.router.navigate(['/project-detail', job.id]);
  }
}
