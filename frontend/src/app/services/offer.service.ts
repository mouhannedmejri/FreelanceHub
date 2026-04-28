import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Offer, OffersResponse, CreateOfferPayload } from '../models/offer.model';

@Injectable({ providedIn: 'root' })
export class OfferService {
  constructor(private http: HttpClient) {}

  getOffers(filters: any = {}): Observable<OffersResponse> {
    let params = new HttpParams();
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
        params = params.set(key, filters[key]);
      }
    });
    return this.http.get<OffersResponse>(`${environment.apiUrl}/offers/`, { params });
  }

  getMyOffers(filters: any = {}): Observable<OffersResponse> {
    let params = new HttpParams();
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
        params = params.set(key, filters[key]);
      }
    });
    return this.http.get<OffersResponse>(`${environment.apiUrl}/offers/mine`, { params });
  }

  getOffer(id: number): Observable<{ offer: Offer }> {
    return this.http.get<{ offer: Offer }>(`${environment.apiUrl}/offers/${id}`);
  }

  createOffer(payload: CreateOfferPayload): Observable<{ offer: Offer }> {
    return this.http.post<{ offer: Offer }>(`${environment.apiUrl}/offers/`, payload);
  }
}
