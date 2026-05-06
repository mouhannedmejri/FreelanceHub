import { Component, OnInit } from '@angular/core';
import { ClientService } from '../../services/client.service';
import { ToastController, AlertController } from '@ionic/angular';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { RecommendationService } from '../../services/recommendation.service';

@Component({
  selector: 'app-client-dashboard',
  templateUrl: './client-dashboard.page.html',
  styleUrls: ['./client-dashboard.page.scss'],
  standalone: false,
})
export class ClientDashboardPage implements OnInit {
  currentTab: 'overview' | 'active' | 'history' = 'overview';
  currentDate = new Date();
  
  // Dashboard data
  stats: any = null;
  activeProjects: any[] = [];
  recentOffers: any[] = [];
  pendingProposals: any[] = [];
  recentActivity: any[] = [];
  recommendedOffers: any[] = [];
  isLoadingDashboard = false;

  // Active Projects Tab
  activeProjectsList: any[] = [];
  activeProjectsPage = 1;
  hasMoreActiveProjects = true;
  isLoadingActiveProjects = false;

  // History Tab
  historyProjects: any[] = [];
  historySearch = '';
  historyFilter = 'all';
  historyPage = 1;
  hasMoreHistory = true;
  isLoadingHistory = false;

  constructor(
    private clientService: ClientService,
    private toastController: ToastController,
    private alertController: AlertController,
    private router: Router,
    private recommendationService: RecommendationService
  ) {}

  ngOnInit() {
    this.loadDashboard();
    this.loadRecommendations();
  }

  doRefresh(event: any) {
    if (this.currentTab === 'overview') {
      this.loadDashboard(event);
    } else if (this.currentTab === 'active') {
      this.loadActiveProjectsList(true, event);
    } else if (this.currentTab === 'history') {
      this.loadHistory(true, event);
    }
  }

  setTab(tab: 'overview' | 'active' | 'history') {
    this.currentTab = tab;
    if (tab === 'active' && this.activeProjectsList.length === 0) {
      this.loadActiveProjectsList(true);
    } else if (tab === 'history' && this.historyProjects.length === 0) {
      this.loadHistory(true);
    }
  }

  onTabChange(tab: unknown) {
    if (tab === 'overview' || tab === 'active' || tab === 'history') {
      this.setTab(tab);
    }
  }

  loadDashboard(event?: any) {
    this.isLoadingDashboard = true;
    this.clientService.getDashboard().subscribe({
      next: (data) => {
        this.stats = data.stats;
        this.activeProjects = data.active_projects;
        this.recentOffers = data.recent_offers;
        this.pendingProposals = data.pending_proposals;
        this.recentActivity = data.recent_activity;
        this.isLoadingDashboard = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoadingDashboard = false;
        if (event) event.target.complete();
      }
    });
  }

  loadRecommendations() {
    this.recommendationService.getOfferRecommendations(10).subscribe({
      next: (res) => (this.recommendedOffers = res.data || []),
      error: () => (this.recommendedOffers = []),
    });
  }

  // --- ACTIVE PROJECTS ---
  loadActiveProjectsList(reset: boolean = false, event?: any) {
    if (reset) {
      this.activeProjectsPage = 1;
      this.activeProjectsList = [];
      this.hasMoreActiveProjects = true;
    }
    if (!this.hasMoreActiveProjects) {
      if (event) event.target.complete();
      return;
    }
    this.isLoadingActiveProjects = true;
    this.clientService.getProjects('active', this.activeProjectsPage, 10).subscribe({
      next: (data) => {
        if (reset) this.activeProjectsList = data.projects;
        else this.activeProjectsList = [...this.activeProjectsList, ...data.projects];
        this.hasMoreActiveProjects = (this.activeProjectsPage * 10) < data.total;
        this.isLoadingActiveProjects = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoadingActiveProjects = false;
        if (event) event.target.complete();
      }
    });
  }

  loadMoreActive(event: any) {
    this.activeProjectsPage++;
    this.loadActiveProjectsList(false, event);
  }

  // --- HISTORY PROJECTS ---
  onHistorySearchChange(event: any) {
    this.historySearch = event.detail.value;
    this.loadHistory(true);
  }

  setHistoryFilter(status: string) {
    this.historyFilter = status;
    this.loadHistory(true);
  }

  loadHistory(reset: boolean = false, event?: any) {
    if (reset) {
      this.historyPage = 1;
      this.historyProjects = [];
      this.hasMoreHistory = true;
    }
    if (!this.hasMoreHistory) {
      if (event) event.target.complete();
      return;
    }
    this.isLoadingHistory = true;
    // Note: status filtering. The backend takes status. If historySearch is needed, backend should support search.
    // For now, we fetch by status and filter locally if needed, or just let backend support it. 
    // Since backend for getProjects doesn't support search yet, we will just filter locally for the search string.
    this.clientService.getProjects(this.historyFilter, this.historyPage, 10).subscribe({
      next: (data) => {
        let projs = data.projects;
        if (this.historySearch) {
          projs = projs.filter((p: any) => p.title.toLowerCase().includes(this.historySearch.toLowerCase()));
        }
        if (reset) this.historyProjects = projs;
        else this.historyProjects = [...this.historyProjects, ...projs];
        
        // Accurate total requires backend search support, but this is a fallback
        this.hasMoreHistory = (this.historyPage * 10) < data.total;
        this.isLoadingHistory = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoadingHistory = false;
        if (event) event.target.complete();
      }
    });
  }

  loadMoreHistory(event: any) {
    this.historyPage++;
    this.loadHistory(false, event);
  }

  // --- NAVIGATION & ACTIONS ---
  goToOfferProposals(offerId: string) {
    this.router.navigate(['/offer-proposals', offerId]);
  }

  goToProjectDetails(projectId: string) {
    this.router.navigate(['/project-detail', projectId]);
  }

  goToRecommendedOffer(offer: any) {
    this.recommendationService.trackInteraction({
      item_id: offer.id,
      item_type: 'offer',
      recommendation_type: 'offers',
      action: 'click',
      score: offer?.recommendation?.score,
      reason: offer?.recommendation?.why_recommended,
    }).subscribe({ error: () => {} });
    this.router.navigate(['/project-detail', offer.id]);
  }

  hideRecommendedOffer(offer: any) {
    this.recommendationService.notInterested(String(offer.id), 'offer').subscribe({
      next: () => {
        this.recommendedOffers = this.recommendedOffers.filter((o) => String(o.id) !== String(offer.id));
      },
      error: () => {},
    });
  }

  async showRecommendationReason(reason: string) {
    const toast = await this.toastController.create({
      message: reason || 'Recommended using your interests, budget fit, recency and competition.',
      duration: 2200,
      color: 'medium',
      position: 'top',
    });
    await toast.present();
  }

  sendMessage(freelancerId: string) {
    this.toastController.create({ message: 'Ouverture de la messagerie', duration: 2000 }).then(t => t.present());
  }

  getMathMax(a: number, b: number): number {
    return Math.max(a, b);
  }

  getDaysElapsed(startedAt: string, deadline: string): number {
    if (!startedAt || !deadline) return 0;
    const start = new Date(startedAt).getTime();
    const end = new Date(deadline).getTime();
    const now = new Date().getTime();
    if (now > end) return 100;
    if (now < start) return 0;
    return Math.floor(((now - start) / (end - start)) * 100);
  }

  getDaysRemaining(deadline: string): number {
    if (!deadline) return 0;
    const end = new Date(deadline).getTime();
    const now = new Date().getTime();
    const diff = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
    return diff > 0 ? diff : 0;
  }

  // ── RING CHART ────────────────────────
  get ringOnTrack(): number {
    return this.stats?.active_projects || 0;
  }
  get ringCompleted(): number {
    return this.stats?.completed_projects || 0;
  }
  get ringTotal(): number {
    return this.ringOnTrack + this.ringCompleted + (this.stats?.at_risk || 0);
  }
  get ringOnTrackPct(): number {
    return this.ringTotal ? Math.round((this.ringOnTrack / this.ringTotal) * 100) : 0;
  }
  get ringCompletedPct(): number {
    return this.ringTotal ? Math.round((this.ringCompleted / this.ringTotal) * 100) : 0;
  }

  getRingDashArray(pct: number): string {
    const circumference = 2 * Math.PI * 42;
    const filled = (pct / 100) * circumference;
    return `${filled} ${circumference - filled}`;
  }

  getRingOffset(prevPct: number): number {
    const circumference = 2 * Math.PI * 42;
    return -(prevPct / 100) * circumference;
  }

  // ── BUDGET UTILIZATION ───────────────
  get totalBudget(): number {
    return this.stats?.total_spent || 0;
  }
  get budgetUsedPct(): number {
    const max = Math.max(this.totalBudget, 1);
    const active = (this.stats?.active_budget || this.stats?.total_spent || 0);
    return Math.min(Math.round((active / max) * 100), 100);
  }

  // ── FAVORITE FREELANCERS ─────────────
  get favoriteFreelancers(): any[] {
    const seen = new Set<string>();
    const result: any[] = [];
    for (const p of this.activeProjects) {
      const fId = p.freelancer?.id || p.freelancer_id;
      if (fId && !seen.has(fId)) {
        seen.add(fId);
        result.push({
          id: fId,
          full_name: p.freelancer?.full_name || 'Freelancer',
          avatar_initials: p.freelancer?.avatar_initials || '?'
        });
      }
    }
    return result;
  }

  goToFreelancerProfile(userId: string) {
    this.router.navigate(['/home/profile'], { queryParams: { userId } });
  }
}
