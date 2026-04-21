import { Component, OnInit } from '@angular/core';
import { ServiceService } from '../../services/service.service';
import { Service } from '../../models/service.model';

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

  categories = [
    { label: 'Tous', value: '' },
    { label: 'Développement', value: 'Développement' },
    { label: 'Design', value: 'Design' },
    { label: 'Marketing', value: 'Marketing' },
    { label: 'Rédaction', value: 'Rédaction' },
  ];

  private searchTimeout: any;

  constructor(private serviceService: ServiceService) {}

  ngOnInit() {
    this.loadServices();
  }

  loadServices(append = false) {
    if (this.isLoading) return;
    this.isLoading = true;

    this.serviceService
      .getServices({
        category: this.selectedCategory,
        search: this.searchTerm,
        page: this.page,
      })
      .subscribe({
        next: (data) => {
          if (append) {
            this.services = [...this.services, ...data.services];
          } else {
            this.services = data.services;
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
        category: this.selectedCategory,
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
    this.selectedCategory = value;
    this.page = 1;
    this.services = [];
    this.loadServices();
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
        category: this.selectedCategory,
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
}
