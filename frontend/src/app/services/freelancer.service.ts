import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface FreelancerSearchParams {
  q?: string;
  skills?: string[];
  min_rating?: number;
  max_price?: number;
  category?: string;
  location?: string;
  availability?: string;
  sort_by?: 'rating' | 'reviews' | 'price_asc' | 'recent_activity';
  limit?: number;
  skip?: number;
}

@Injectable({
  providedIn: 'root'
})
export class FreelancerService {
  private searchCache = new Map<string, any>();

  constructor(private http: HttpClient) {}

  getDashboard(): Observable<any> {
    return this.http.get<any>(`${environment.apiUrl}/freelancer/dashboard`);
  }

  getProjects(status: string = 'all', page: number = 1, perPage: number = 10): Observable<any> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('per_page', perPage.toString());
    
    if (status !== 'all') {
      params = params.set('status', status);
    }
    
    return this.http.get<any>(`${environment.apiUrl}/freelancer/projects`, { params });
  }

  getEarnings(period: string = 'month'): Observable<any> {
    const params = new HttpParams().set('period', period);
    return this.http.get<any>(`${environment.apiUrl}/freelancer/earnings`, { params });
  }

  getReviews(page: number = 1, perPage: number = 10): Observable<any> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('per_page', perPage.toString());
      
    return this.http.get<any>(`${environment.apiUrl}/freelancer/reviews`, { params });
  }

  searchFreelancers(params: FreelancerSearchParams): Observable<any> {
    let httpParams = new HttpParams();
    const keys = Object.keys(params).sort();

    keys.forEach((key) => {
      const typedKey = key as keyof FreelancerSearchParams;
      const value = params[typedKey];
      if (value === undefined || value === null || value === '') return;

      if (Array.isArray(value)) {
        value.forEach((entry) => {
          httpParams = httpParams.append('skills[]', String(entry));
        });
      } else {
        httpParams = httpParams.set(key, String(value));
      }
    });

    const cacheKey = httpParams.toString();
    const cached = this.searchCache.get(cacheKey);
    if (cached) {
      return of(cached);
    }

    return this.http
      .get<any>(`${environment.apiUrl}/freelancers/search`, { params: httpParams })
      .pipe(tap((res) => this.searchCache.set(cacheKey, res)));
  }
}
