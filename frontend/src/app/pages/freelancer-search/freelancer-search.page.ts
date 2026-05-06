import { Component, OnDestroy, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators';
import { FreelancerService, FreelancerSearchParams } from '../../services/freelancer.service';

@Component({
  selector: 'app-freelancer-search',
  templateUrl: './freelancer-search.page.html',
  styleUrls: ['./freelancer-search.page.scss'],
  standalone: false,
})
export class FreelancerSearchPage implements OnInit, OnDestroy {
  categories = ['All', 'Designers', 'Developers', 'Writers', 'Marketers'];
  sortOptions = [
    { label: 'Rating', value: 'rating' },
    { label: 'Reviews', value: 'reviews' },
    { label: 'Price (low to high)', value: 'price_asc' },
    { label: 'Recent Activity', value: 'recent_activity' },
  ];

  searchTerm = '';
  selectedCategory = 'All';
  selectedSkills: string[] = [];
  availableSkills = ['UI/UX', 'Angular', 'React', 'SEO', 'Copywriting', 'Branding'];
  minRating = 0;
  maxPrice?: number;
  availability = '';
  location = '';
  sortBy: FreelancerSearchParams['sort_by'] = 'rating';

  freelancers: any[] = [];
  suggestions: string[] = [];
  loading = false;
  isEmpty = false;
  total = 0;
  limit = 12;
  skip = 0;

  private destroy$ = new Subject<void>();
  private searchTrigger$ = new Subject<string>();

  constructor(private freelancerService: FreelancerService, private router: Router) {}

  ngOnInit(): void {
    this.searchTrigger$
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntil(this.destroy$))
      .subscribe(() => {
        this.skip = 0;
        this.fetchFreelancers(false);
      });

    this.fetchFreelancers(false);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onSearchInput(): void {
    this.searchTrigger$.next(this.searchTerm);
  }

  selectCategory(category: string): void {
    this.selectedCategory = category;
    this.skip = 0;
    this.fetchFreelancers(false);
  }

  toggleSkill(skill: string): void {
    if (this.selectedSkills.includes(skill)) {
      this.selectedSkills = this.selectedSkills.filter((s) => s !== skill);
    } else {
      this.selectedSkills = [...this.selectedSkills, skill];
    }
    this.skip = 0;
    this.fetchFreelancers(false);
  }

  setRating(minRating: number): void {
    this.minRating = minRating;
    this.skip = 0;
    this.fetchFreelancers(false);
  }

  setAvailability(value: string): void {
    this.availability = this.availability === value ? '' : value;
    this.skip = 0;
    this.fetchFreelancers(false);
  }

  applyPriceFilter(value: string): void {
    this.maxPrice = value ? Number(value) : undefined;
    this.skip = 0;
    this.fetchFreelancers(false);
  }

  applyLocation(): void {
    this.skip = 0;
    this.fetchFreelancers(false);
  }

  changeSort(): void {
    this.skip = 0;
    this.fetchFreelancers(false);
  }

  loadMore(event: any): void {
    this.skip += this.limit;
    this.fetchFreelancers(true, event);
  }

  onViewProfile(freelancer: any): void {
    this.router.navigate(['/home/profile'], { queryParams: { userId: freelancer.id } });
  }

  onContact(freelancer: any): void {
    this.router.navigate(['/home/messages'], { queryParams: { userId: freelancer.id } });
  }

  private fetchFreelancers(append: boolean, event?: any): void {
    this.loading = !append;

    const params: FreelancerSearchParams = {
      q: this.searchTerm,
      skills: this.selectedSkills,
      min_rating: this.minRating || undefined,
      max_price: this.maxPrice,
      category: this.selectedCategory === 'All' ? '' : this.selectedCategory,
      sort_by: this.sortBy,
      availability: this.availability,
      location: this.location,
      limit: this.limit,
      skip: this.skip,
    };

    this.freelancerService.searchFreelancers(params).subscribe({
      next: (res) => {
        this.freelancers = append ? [...this.freelancers, ...res.data] : res.data;
        this.suggestions = (res.suggestions || []).map((s: any) => s.text);
        this.total = res.meta?.total || 0;
        this.isEmpty = this.freelancers.length === 0;
        this.loading = false;
        if (event) {
          event.target.complete();
        }
      },
      error: () => {
        this.loading = false;
        this.isEmpty = true;
        if (event) {
          event.target.complete();
        }
      },
    });
  }
}
