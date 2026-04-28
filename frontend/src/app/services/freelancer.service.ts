import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FreelancerService {
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
}
