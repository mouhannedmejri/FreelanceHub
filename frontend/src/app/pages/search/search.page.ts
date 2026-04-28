import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { Router } from '@angular/router';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { Subject } from 'rxjs';

@Component({
  selector: 'app-search',
  templateUrl: './search.page.html',
  styleUrls: ['./search.page.scss'],
  standalone: false
})
export class SearchPage implements OnInit {
  searchQuery = '';
  filterType = '';
  results: any[] = [];
  page = 1;
  hasMore = false;
  loading = false;
  
  private searchSubject = new Subject<string>();

  constructor(private http: HttpClient, private router: Router) {
    this.searchSubject.pipe(
      debounceTime(400),
      distinctUntilChanged()
    ).subscribe(() => {
      this.resetAndSearch();
    });
  }

  ngOnInit() {
    this.loadResults();
  }

  onSearch() {
    this.searchSubject.next(this.searchQuery);
  }

  setFilter(type: string) {
    if (this.filterType !== type) {
      this.filterType = type;
      this.resetAndSearch();
    }
  }

  resetAndSearch() {
    this.page = 1;
    this.results = [];
    this.loadResults();
  }

  loadResults(event?: any) {
    if (this.page === 1) this.loading = true;
    
    let url = `${environment.apiUrl}/api/search?page=${this.page}&limit=20`;
    if (this.searchQuery) url += `&q=${encodeURIComponent(this.searchQuery)}`;
    if (this.filterType) url += `&type=${this.filterType}`;

    this.http.get<any>(url).subscribe({
      next: (res) => {
        if (this.page === 1) {
          this.results = res.data;
        } else {
          this.results = [...this.results, ...res.data];
        }
        this.hasMore = res.meta.has_more;
        this.loading = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.loading = false;
        if (event) event.target.complete();
      }
    });
  }

  loadMore(event: any) {
    if (!this.hasMore) {
      event.target.complete();
      return;
    }
    this.page++;
    this.loadResults(event);
  }

  goToDetail(item: any) {
    if (item.result_type === 'user') {
      this.router.navigate(['/home/profile'], { queryParams: { id: item.id }});
    } else if (item.result_type === 'offer') {
      this.router.navigate(['/project-detail', item.id]);
    } else if (item.result_type === 'service') {
      // You can implement navigation to service details
      // this.router.navigate(['/service-detail', item.id]);
    }
  }
}
