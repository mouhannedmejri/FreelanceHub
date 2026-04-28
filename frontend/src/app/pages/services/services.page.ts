import { Component, OnInit } from '@angular/core';
import { ServiceService } from '../../services/service.service';
import { Service } from '../../models/service.model';
import { Router } from '@angular/router';

interface FilterState {
  category: string;
  budgetMin: number;
  budgetMax: number;
  level: string;
  remoteOnly: boolean;
}

@Component({
  selector: 'app-services',
  templateUrl: './services.page.html',
  styleUrls: ['./services.page.scss'],
  standalone: false,
})
export class ServicesPage implements OnInit {
  services: Service[] = [];
  totalServices = 0;
  page = 1;
  hasMore = true;
  isLoading = false;
  searchTerm = '';
  selectedCategory = '';

  // Filter bar
  filters: FilterState = {
    category: '',
    budgetMin: 0,
    budgetMax: 10000,
    level: '',
    remoteOnly: false
  };
  activeFilterSheet: string | null = null;
  savedServices: Set<string | number> = new Set();

  categories = [
    { label: 'Tous', value: '' },
    { label: 'Développement', value: 'Développement' },
    { label: 'Design', value: 'Design' },
    { label: 'Marketing', value: 'Marketing' },
    { label: 'Rédaction', value: 'Rédaction' },
  ];

  levels = [
    { label: 'Tous', value: '' },
    { label: 'Entry', value: 'Débutant' },
    { label: 'Mid', value: 'Intermédiaire' },
    { label: 'Expert', value: 'Expert' },
  ];

  private searchTimeout: any;

  constructor(private serviceService: ServiceService, private router: Router) {}

  ngOnInit() {
    this.loadServices();
  }

  loadServices(append = false) {
    if (this.isLoading) return;
    this.isLoading = true;

    this.serviceService
      .getServices({
        category: this.filters.category || this.selectedCategory,
        search: this.searchTerm,
        page: this.page,
      })
      .subscribe({
        next: (data) => {
          let filtered = data.services;

          // Client-side filters for level and budget
          if (this.filters.level) {
            filtered = filtered.filter(s => s.level === this.filters.level);
          }
          if (this.filters.budgetMax < 10000) {
            filtered = filtered.filter(s => s.price_from <= this.filters.budgetMax);
          }
          if (this.filters.budgetMin > 0) {
            filtered = filtered.filter(s => s.price_from >= this.filters.budgetMin);
          }

          if (append) {
            this.services = [...this.services, ...filtered];
          } else {
            this.services = filtered;
          }
          this.totalServices = data.total;
          this.hasMore = data.has_more;
          this.isLoading = false;
        },
        error: () => {
          this.isLoading = false;
        },
      });
  }

  doRefresh(event: any) {
    this.page = 1;
    this.isLoading = true;
    this.serviceService
      .getServices({
        category: this.filters.category || this.selectedCategory,
        search: this.searchTerm,
        page: this.page,
      })
      .subscribe({
        next: (data) => {
          this.services = data.services;
          this.totalServices = data.total;
          this.hasMore = data.has_more;
          this.isLoading = false;
          event.target.complete();
        },
        error: () => {
          this.isLoading = false;
          event.target.complete();
        },
      });
  }

  selectCategory(value: string) {
    this.filters.category = value;
    this.selectedCategory = value;
    this.page = 1;
    this.services = [];
    this.loadServices();
    this.closeFilterSheet();
  }

  onSearch() {
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(() => {
      this.page = 1;
      this.services = [];
      this.loadServices();
    }, 300);
  }

  loadMore(event: any) {
    this.page++;
    this.serviceService
      .getServices({
        category: this.filters.category || this.selectedCategory,
        search: this.searchTerm,
        page: this.page,
      })
      .subscribe({
        next: (data) => {
          this.services = [...this.services, ...data.services];
          this.hasMore = data.has_more;
          event.target.complete();
          if (!data.has_more) {
            event.target.disabled = true;
          }
        },
        error: () => {
          event.target.complete();
        },
      });
  }

  // ── FILTER BAR ────────────────────────────
  toggleFilterSheet(sheet: string) {
    this.activeFilterSheet = this.activeFilterSheet === sheet ? null : sheet;
  }

  closeFilterSheet() {
    this.activeFilterSheet = null;
  }

  setLevel(level: string) {
    this.filters.level = level;
    this.page = 1;
    this.services = [];
    this.loadServices();
    this.closeFilterSheet();
  }

  setBudgetRange(min: number, max: number) {
    this.filters.budgetMin = min;
    this.filters.budgetMax = max;
    this.page = 1;
    this.services = [];
    this.loadServices();
    this.closeFilterSheet();
  }

  toggleRemote() {
    this.filters.remoteOnly = !this.filters.remoteOnly;
    this.page = 1;
    this.services = [];
    this.loadServices();
  }

  clearFilter(key: string) {
    switch (key) {
      case 'category':
        this.filters.category = '';
        this.selectedCategory = '';
        break;
      case 'level':
        this.filters.level = '';
        break;
      case 'budget':
        this.filters.budgetMin = 0;
        this.filters.budgetMax = 10000;
        break;
      case 'remote':
        this.filters.remoteOnly = false;
        break;
    }
    this.page = 1;
    this.services = [];
    this.loadServices();
  }

  get hasActiveFilters(): boolean {
    return !!(this.filters.category || this.filters.level || this.filters.budgetMax < 10000 || this.filters.budgetMin > 0 || this.filters.remoteOnly);
  }

  get activeFilterChips(): { key: string; label: string }[] {
    const chips: { key: string; label: string }[] = [];
    if (this.filters.category) chips.push({ key: 'category', label: this.filters.category });
    if (this.filters.level) chips.push({ key: 'level', label: this.filters.level });
    if (this.filters.budgetMin > 0 || this.filters.budgetMax < 10000) {
      chips.push({ key: 'budget', label: `${this.filters.budgetMin}€ – ${this.filters.budgetMax}€` });
    }
    if (this.filters.remoteOnly) chips.push({ key: 'remote', label: 'Remote' });
    return chips;
  }

  // ── CARD HELPERS ──────────────────────────
  toggleSave(service: Service) {
    const id = service.id;
    if (this.savedServices.has(id)) {
      this.savedServices.delete(id);
    } else {
      this.savedServices.add(id);
    }
  }

  isSaved(service: Service): boolean {
    return this.savedServices.has(service.id);
  }

  getTimeAgo(): string {
    const minutes = Math.floor(Math.random() * 55) + 5;
    return `Il y a ${minutes} min`;
  }

  getInitials(name: string): string {
    if (!name) return '?';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  }

  getStars(rating: number): string[] {
    const stars: string[] = [];
    for (let i = 1; i <= 5; i++) {
      if (i <= Math.floor(rating)) {
        stars.push('star');
      } else if (i - 0.5 <= rating) {
        stars.push('star-half');
      } else {
        stars.push('star-outline');
      }
    }
    return stars;
  }

  openFreelancerProfile(service: Service) {
    this.router.navigate(['/home/profile'], {
      queryParams: { userId: service.freelancer_id },
    });
  }
}
