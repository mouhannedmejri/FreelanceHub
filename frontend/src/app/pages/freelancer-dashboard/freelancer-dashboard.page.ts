import { Component, OnInit, OnDestroy } from '@angular/core';
import { FreelancerService } from '../../services/freelancer.service';
import { AuthService } from '../../services/auth.service';
import { ProjectService } from '../../services/project.service';
import { ToastController, AlertController } from '@ionic/angular';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { RecommendationService } from '../../services/recommendation.service';

@Component({
  selector: 'app-freelancer-dashboard',
  templateUrl: './freelancer-dashboard.page.html',
  styleUrls: ['./freelancer-dashboard.page.scss'],
  standalone: false,
})
export class FreelancerDashboardPage implements OnInit, OnDestroy {
  user: any = null;
  private userSub!: Subscription;
  
  currentTab: 'overview' | 'projects' | 'earnings' | 'reviews' = 'overview';
  
  // Dashboard data
  stats: any = null;
  activeProjects: any[] = [];
  recentProposals: any[] = [];
  recentReviews: any[] = [];
  isLoadingDashboard = false;

  // Upcoming milestones
  upcomingMilestones: any[] = [];

  // Projects Tab
  projectsList: any[] = [];
  projectsFilter = 'all';
  projectsPage = 1;
  hasMoreProjects = true;
  isLoadingProjects = false;

  // Earnings Tab
  earningsPeriod = 'month';
  earningsData: any = null;
  isLoadingEarnings = false;

  // Reviews Tab
  reviewsList: any[] = [];
  reviewsPage = 1;
  hasMoreReviews = true;
  isLoadingReviews = false;
  reviewsTotalCount = 0;

  // Sparkline data for earnings mini-chart
  sparklinePoints = '';
  recommendedOpportunities: any[] = [];

  constructor(
    private freelancerService: FreelancerService,
    private authService: AuthService,
    private projectService: ProjectService,
    private toastController: ToastController,
    private alertController: AlertController,
    private router: Router,
    private recommendationService: RecommendationService
  ) {}

  ngOnInit() {
    this.userSub = this.authService.currentUser$.subscribe(user => {
      this.user = user;
    });
    this.loadDashboard();
    this.loadUpcomingMilestones();
    this.loadOpportunities();
  }

  ngOnDestroy() {
    if (this.userSub) this.userSub.unsubscribe();
  }

  doRefresh(event: any) {
    if (this.currentTab === 'overview') {
      this.loadDashboard(event);
    } else if (this.currentTab === 'projects') {
      this.loadProjects(true, event);
    } else if (this.currentTab === 'earnings') {
      this.loadEarnings(event);
    } else if (this.currentTab === 'reviews') {
      this.loadReviews(true, event);
    }
  }

  setTab(tab: 'overview' | 'projects' | 'earnings' | 'reviews') {
    this.currentTab = tab;
    if (tab === 'projects' && this.projectsList.length === 0) {
      this.loadProjects(true);
    } else if (tab === 'earnings' && !this.earningsData) {
      this.loadEarnings();
    } else if (tab === 'reviews' && this.reviewsList.length === 0) {
      this.loadReviews(true);
    }
  }

  onTabChange(tab: unknown) {
    if (tab === 'overview' || tab === 'projects' || tab === 'earnings' || tab === 'reviews') {
      this.setTab(tab);
    }
  }

  loadDashboard(event?: any) {
    this.isLoadingDashboard = true;
    this.freelancerService.getDashboard().subscribe({
      next: (data) => {
        this.stats = data.stats;
        this.activeProjects = data.active_projects;
        this.recentProposals = data.recent_proposals;
        this.recentReviews = data.recent_reviews;
        this.isLoadingDashboard = false;
        if (event) event.target.complete();
        // Generate sparkline after earnings load
        this.loadEarningsForSparkline();
      },
      error: () => {
        this.isLoadingDashboard = false;
        if (event) event.target.complete();
      }
    });
  }

  loadUpcomingMilestones() {
    this.projectService.getUpcomingMilestones().subscribe({
      next: (res) => (this.upcomingMilestones = res.milestones || []),
      error: () => (this.upcomingMilestones = []),
    });
  }

  loadEarningsForSparkline() {
    this.freelancerService.getEarnings('month').subscribe({
      next: (data) => {
        if (data.by_month && data.by_month.length > 0) {
          this.generateSparkline(data.by_month.map((m: any) => m.amount));
        }
      }
    });
  }

  loadOpportunities() {
    this.recommendationService.getOpportunityRecommendations(10).subscribe({
      next: (res) => (this.recommendedOpportunities = res.data || []),
      error: () => (this.recommendedOpportunities = []),
    });
  }

  generateSparkline(values: number[]) {
    if (!values.length) return;
    const max = Math.max(...values, 1);
    const w = 120;
    const h = 40;
    const step = w / (values.length - 1 || 1);
    const points = values.map((v, i) => {
      const x = i * step;
      const y = h - (v / max) * h;
      return `${x},${y}`;
    });
    this.sparklinePoints = points.join(' ');
  }

  // --- PROJECTS TAB ---
  setProjectsFilter(status: string) {
    this.projectsFilter = status;
    this.loadProjects(true);
  }

  loadProjects(reset: boolean = false, event?: any) {
    if (reset) {
      this.projectsPage = 1;
      this.projectsList = [];
      this.hasMoreProjects = true;
    }
    if (!this.hasMoreProjects) {
      if (event) event.target.complete();
      return;
    }
    this.isLoadingProjects = true;
    this.freelancerService.getProjects(this.projectsFilter, this.projectsPage, 10).subscribe({
      next: (data) => {
        if (reset) this.projectsList = data.projects;
        else this.projectsList = [...this.projectsList, ...data.projects];
        this.hasMoreProjects = (this.projectsPage * 10) < data.total;
        this.isLoadingProjects = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoadingProjects = false;
        if (event) event.target.complete();
      }
    });
  }

  loadMoreProjects(event: any) {
    this.projectsPage++;
    this.loadProjects(false, event);
  }

  // --- EARNINGS TAB ---
  setEarningsPeriod(period: string) {
    this.earningsPeriod = period;
    this.loadEarnings();
  }

  onEarningsPeriodChange(period: unknown) {
    if (period === 'month' || period === 'year') {
      this.setEarningsPeriod(period);
    }
  }

  loadEarnings(event?: any) {
    this.isLoadingEarnings = true;
    this.freelancerService.getEarnings(this.earningsPeriod).subscribe({
      next: (data) => {
        this.earningsData = data;
        this.isLoadingEarnings = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoadingEarnings = false;
        if (event) event.target.complete();
      }
    });
  }

  getMaxChartAmount(): number {
    if (!this.earningsData?.by_month || this.earningsData.by_month.length === 0) return 1;
    let max = 0;
    for (let item of this.earningsData.by_month) {
      if (item.amount > max) max = item.amount;
    }
    return max > 0 ? max : 1;
  }

  // --- REVIEWS TAB ---
  loadReviews(reset: boolean = false, event?: any) {
    if (reset) {
      this.reviewsPage = 1;
      this.reviewsList = [];
      this.hasMoreReviews = true;
    }
    if (!this.hasMoreReviews) {
      if (event) event.target.complete();
      return;
    }
    this.isLoadingReviews = true;
    this.freelancerService.getReviews(this.reviewsPage, 10).subscribe({
      next: (data) => {
        if (reset) this.reviewsList = data.reviews;
        else this.reviewsList = [...this.reviewsList, ...data.reviews];
        this.reviewsTotalCount = data.total;
        this.hasMoreReviews = (this.reviewsPage * 10) < data.total;
        this.isLoadingReviews = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoadingReviews = false;
        if (event) event.target.complete();
      }
    });
  }

  loadMoreReviews(event: any) {
    this.reviewsPage++;
    this.loadReviews(false, event);
  }

  getStarArray(rating: number): number[] {
    const fullStars = Math.floor(rating || 0);
    return Array(fullStars).fill(0);
  }
  
  getEmptyStarArray(rating: number): number[] {
    const fullStars = Math.floor(rating || 0);
    return Array(5 - fullStars).fill(0);
  }

  // --- ACTIONS ---
  goToProjectDetails(projectId: string) {
    this.router.navigate(['/project-detail', projectId]);
  }

  goToOpportunity(offer: any) {
    this.recommendationService.trackInteraction({
      item_id: offer.id,
      item_type: 'offer',
      recommendation_type: 'opportunities',
      action: 'click',
      score: offer?.recommendation?.score,
      reason: offer?.recommendation?.why_recommended,
    }).subscribe({ error: () => {} });
    this.router.navigate(['/project-detail', offer.id]);
  }

  dismissOpportunity(offer: any) {
    this.recommendationService.notInterested(String(offer.id), 'opportunity').subscribe({
      next: () => {
        this.recommendedOpportunities = this.recommendedOpportunities.filter((o) => String(o.id) !== String(offer.id));
      },
      error: () => {},
    });
  }

  async showOpportunityReason(reason: string) {
    const toast = await this.toastController.create({
      message: reason || 'Recommended based on your skills and market fit.',
      duration: 2200,
      color: 'medium',
      position: 'top',
    });
    await toast.present();
  }

  sendMessage(clientId: string) {
    this.toastController.create({ message: 'Ouverture de la messagerie', duration: 2000 }).then(t => t.present());
  }

  navigateTo(path: string) {
    this.router.navigate([path]);
  }

  async requestWithdraw() {
    const alert = await this.alertController.create({
      header: 'Retrait de fonds',
      message: 'Entrez le montant à retirer',
      inputs: [{ name: 'amount', type: 'number', placeholder: 'Montant (€)', min: 10 }],
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        { text: 'Confirmer', handler: (data) => {
          this.toastController.create({ message: `Demande de retrait de ${data.amount}€ envoyée`, duration: 3000, color: 'success' }).then(t => t.present());
        }}
      ]
    });
    await alert.present();
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

  get formattedEarnings(): string {
    const e = this.stats?.total_earned || 0;
    if (e >= 1000) return `${Math.round(e / 1000)}K`;
    return `${e}`;
  }
}
