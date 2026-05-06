import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class RecommendationService {
  constructor(private http: HttpClient) {}

  getOfferRecommendations(limit = 10, skip = 0): Observable<any> {
    const params = new HttpParams().set('limit', String(limit)).set('skip', String(skip));
    return this.http.get<any>(`${environment.apiUrl}/recommendations/offers`, { params });
  }

  getFreelancerRecommendations(limit = 10, skip = 0): Observable<any> {
    const params = new HttpParams().set('limit', String(limit)).set('skip', String(skip));
    return this.http.get<any>(`${environment.apiUrl}/recommendations/freelancers`, { params });
  }

  getOpportunityRecommendations(limit = 10, skip = 0): Observable<any> {
    const params = new HttpParams().set('limit', String(limit)).set('skip', String(skip));
    return this.http.get<any>(`${environment.apiUrl}/recommendations/opportunities`, { params });
  }

  trackInteraction(payload: any): Observable<any> {
    return this.http.post<any>(`${environment.apiUrl}/recommendations/track`, payload);
  }

  notInterested(itemId: string, itemType: 'offer' | 'freelancer' | 'opportunity'): Observable<any> {
    return this.http.post<any>(`${environment.apiUrl}/recommendations/not-interested`, {
      item_id: itemId,
      item_type: itemType,
    });
  }
}
