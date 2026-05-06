import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of, tap, map } from 'rxjs';
import { environment } from '../../environments/environment';
import { FullProfile } from '../models/profile.model';
import { User } from '../models/user.model';

@Injectable({ providedIn: 'root' })
export class ProfileService {
  private profileSubject = new BehaviorSubject<FullProfile | null>(null);
  public profile$ = this.profileSubject.asObservable();
  private loaded = false;

  constructor(private http: HttpClient) {}

  get cachedProfile(): FullProfile | null {
    return this.profileSubject.value;
  }

  fetchProfile(userId: number | string, forceRefresh = false): Observable<FullProfile> {
    if (this.loaded && this.cachedProfile && !forceRefresh) {
      return of(this.cachedProfile);
    }
    return this.http.get<FullProfile>(`${environment.apiUrl}/users/${userId}/profile`).pipe(
      tap((profile) => {
        this.profileSubject.next(profile);
        this.loaded = true;
      })
    );
  }

  fetchProfileByUsername(username: string): Observable<FullProfile> {
    return this.http.get<FullProfile>(`${environment.apiUrl}/users/freelancer/${username}`);
  }

  updateProfile(data: Record<string, any>): Observable<FullProfile> {
    return this.http
      .put<FullProfile>(`${environment.apiUrl}/users/profile`, data)
      .pipe(tap((profile) => this.profileSubject.next(profile)));
  }

  uploadCV(file: File): Observable<FullProfile> {
    const formData = new FormData();
    formData.append('cv', file);
    return this.http
      .post<FullProfile>(`${environment.apiUrl}/users/profile/cv`, formData)
      .pipe(tap((profile) => this.profileSubject.next(profile)));
  }

  clearCache(): void {
    this.profileSubject.next(null);
    this.loaded = false;
  }

  updateOnboardingPreferences(payload: {
    preferences: Record<string, any>;
    onboarding_complete: boolean;
    interests?: string[];
  }): Observable<{ user: User }> {
    return this.http.put<{ user: User }>(`${environment.apiUrl}/users/onboarding`, payload);
  }

  toggleFollow(userId: string | number): Observable<{ action: string; follower_count: number }> {
    return this.http.post<{ action: string; follower_count: number }>(`${environment.apiUrl}/follow/${userId}`, {});
  }

  getFollowers(userId: string | number, page = 1, limit = 20): Observable<{ data: any[]; meta: any }> {
    return this.http.get<{ data: any[]; meta: any }>(`${environment.apiUrl}/follow/${userId}/followers`, {
      params: { page: String(page), limit: String(limit) },
    });
  }

  getFollowingFeed(limit = 10, page = 1): Observable<{ feed: any[]; total: number }> {
    return this.http.get<{ data: any[]; meta: any }>(`${environment.apiUrl}/follow/feed`, {
      params: { limit: limit.toString(), page: String(page) },
    }).pipe(
      map((res) => ({
        feed: res.data || [],
        total: res.meta?.total || 0,
      }))
    );
  }

  updateInterests(interests: string[]): Observable<{ user: User }> {
    return this.http.put<{ user: User }>(`${environment.apiUrl}/users/interests`, { interests });
  }
}
