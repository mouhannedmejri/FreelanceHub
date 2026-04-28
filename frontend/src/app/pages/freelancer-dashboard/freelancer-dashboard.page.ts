import { Component, OnInit, OnDestroy } from '@angular/core';
import { FreelancerService } from '../../services/freelancer.service';
import { AuthService } from '../../services/auth.service';
import { ToastController, AlertController } from '@ionic/angular';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

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

  constructor(
    private freelancerService: FreelancerService,
    private authService: AuthService,
    private toastController: ToastController,
    private alertController: AlertController,
    private router: Router
  ) {}

  ngOnInit() {
    this.userSub = this.authService.currentUser$.subscribe(user => {
      this.user = user;
    });
    this.loadDashboard();
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
      },
      error: () => {
        this.isLoadingDashboard = false;
        if (event) event.target.complete();
      }
    });
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
    this.toastController.create({ message: 'Détails du projet ' + projectId, duration: 2000 }).then(t => t.present());
  }

  sendMessage(clientId: string) {
    this.toastController.create({ message: 'Ouverture de la messagerie', duration: 2000 }).then(t => t.present());
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
}
