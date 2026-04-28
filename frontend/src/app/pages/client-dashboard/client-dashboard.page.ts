import { Component, OnInit } from '@angular/core';
import { ClientService } from '../../services/client.service';
import { ToastController, AlertController } from '@ionic/angular';
import { Router } from '@angular/router';

@Component({
  selector: 'app-client-dashboard',
  templateUrl: './client-dashboard.page.html',
  styleUrls: ['./client-dashboard.page.scss'],
  standalone: false,
})
export class ClientDashboardPage implements OnInit {
  currentTab: 'overview' | 'active' | 'history' = 'overview';
  
  // Dashboard data
  stats: any = null;
  activeProjects: any[] = [];
  recentOffers: any[] = [];
  pendingProposals: any[] = [];
  recentActivity: any[] = [];
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
    private router: Router
  ) {}

  ngOnInit() {
    this.loadDashboard();
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
    // For now navigate or open modal. Let's just navigate if there is a route, or just show toast
    this.toastController.create({ message: 'Navigation vers le projet ' + projectId, duration: 2000 }).then(t => t.present());
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
}
