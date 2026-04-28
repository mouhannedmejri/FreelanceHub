import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Review } from '../models/review.model';

@Injectable({ providedIn: 'root' })
export class ReviewService {
  constructor(private http: HttpClient) {}

  submitReview(data: Partial<Review>): Observable<{ review: Review }> {
    return this.http.post<{ review: Review }>(`${environment.apiUrl}/reviews`, data);
  }

  getUserReviews(userId: number | string): Observable<{ reviews: Review[] }> {
    return this.http.get<{ reviews: Review[] }>(`${environment.apiUrl}/users/${userId}/reviews`);
  }
}
