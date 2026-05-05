import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
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
    return this.http.get<any>(`${environment.apiUrl}/offers/`, { params }).pipe(
      map(res => {
        const offers: Offer[] = res?.offers ?? res?.data ?? (Array.isArray(res) ? res : []);
        const total: number = res?.total ?? res?.meta?.total ?? offers.length;
        return { offers, total } as OffersResponse;
      }),
      catchError(err => {
        console.error('getOffers error:', err);
        return of({ offers: [], total: 0 } as OffersResponse);
      })
    );
  }

  getMyOffers(filters: any = {}): Observable<OffersResponse> {
    let params = new HttpParams();
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
        params = params.set(key, filters[key]);
      }
    });
    return this.http.get<any>(`${environment.apiUrl}/offers/mine`, { params }).pipe(
      map(res => {
        const offers: Offer[] = res?.offers ?? res?.data ?? (Array.isArray(res) ? res : []);
        const total: number = res?.total ?? res?.meta?.total ?? offers.length;
        return { offers, total } as OffersResponse;
      }),
      catchError(err => {
        console.error('getMyOffers error:', err);
        return of({ offers: [], total: 0 } as OffersResponse);
      })
    );
  }

  getOffer(id: number | string): Observable<{ offer: Offer }> {
    return this.http.get<any>(`${environment.apiUrl}/offers/${id}`).pipe(
      map(res => ({ offer: res?.offer ?? res })),
      catchError(err => {
        console.error('getOffer error:', err);
        return of({ offer: null as any });
      })
    );
  }

  createOffer(payload: CreateOfferPayload): Observable<{ offer: Offer }> {
    return this.http.post<any>(`${environment.apiUrl}/offers/`, payload).pipe(
      map(res => ({ offer: res?.offer ?? res }))
    );
  }
}

