import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of, tap } from 'rxjs';
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

  /**
   * Fetch the profile for a given user ID.
   * Returns cached data unless forceRefresh is true.
   */
  fetchProfile(
    userId: number | string,
    forceRefresh = false
  ): Observable<FullProfile> {
    if (this.loaded && this.cachedProfile && !forceRefresh) {
      return of(this.cachedProfile);
    }
    return this.http
      .get<FullProfile>(`${environment.apiUrl}/users/${userId}/profile`)
      .pipe(
        tap((profile) => {
          this.profileSubject.next(profile);
          this.loaded = true;
        })
      );
  }

  /**
   * Update the current user's profile fields (bio, title, skills, etc.).
   */
  updateProfile(data: Record<string, any>): Observable<FullProfile> {
    return this.http
      .put<FullProfile>(`${environment.apiUrl}/users/profile`, data)
      .pipe(tap((profile) => this.profileSubject.next(profile)));
  }

  /**
   * Upload a CV PDF for the current user.
   */
  uploadCV(file: File): Observable<FullProfile> {
    const formData = new FormData();
    formData.append('cv', file);
    return this.http
      .post<FullProfile>(`${environment.apiUrl}/users/profile/cv`, formData)
      .pipe(tap((profile) => this.profileSubject.next(profile)));
  }

  /** Clear cached profile data (e.g. on logout). */
  clearCache(): void {
    this.profileSubject.next(null);
    this.loaded = false;
  }

  updateOnboardingPreferences(payload: {
    preferences: Record<string, any>;
    onboarding_complete: boolean;
  }): Observable<{ user: User }> {
    return this.http.put<{ user: User }>(
      `${environment.apiUrl}/users/onboarding`,
      payload
    );
  }

  /** Toggle follow/unfollow for a user. */
  toggleFollow(userId: string | number): Observable<{ action: string; follower_count: number }> {
    return this.http.post<{ action: string; follower_count: number }>(
      `${environment.apiUrl}/users/${userId}/follow`, {}
    );
  }

  /** Get followers list for a user. */
  getFollowers(userId: string | number): Observable<{ followers: any[]; total: number }> {
    return this.http.get<{ followers: any[]; total: number }>(
      `${environment.apiUrl}/users/${userId}/followers`
    );
  }

  /** Get the following feed — updates from freelancers the user follows. */
  getFollowingFeed(limit = 10): Observable<{ feed: any[]; total: number }> {
    return this.http.get<{ feed: any[]; total: number }>(
      `${environment.apiUrl}/users/following-feed`,
      { params: { limit: limit.toString() } }
    );
  }
}
