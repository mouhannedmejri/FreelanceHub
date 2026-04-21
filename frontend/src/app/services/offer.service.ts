import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Offer, OffersResponse, CreateOfferPayload } from '../models/offer.model';

@Injectable({ providedIn: 'root' })
export class OfferService {
  constructor(private http: HttpClient) {}

  getOffers(search?: string): Observable<OffersResponse> {
    let params = new HttpParams();
    if (search) {
      params = params.set('search', search);
    }
    return this.http.get<OffersResponse>(`${environment.apiUrl}/offers/`, { params });
  }

  getMyOffers(): Observable<OffersResponse> {
    return this.http.get<OffersResponse>(`${environment.apiUrl}/offers/mine`);
  }

  getOffer(id: number): Observable<{ offer: Offer }> {
    return this.http.get<{ offer: Offer }>(`${environment.apiUrl}/offers/${id}`);
  }

  createOffer(payload: CreateOfferPayload): Observable<{ offer: Offer }> {
    return this.http.post<{ offer: Offer }>(`${environment.apiUrl}/offers/`, payload);
  }
}
