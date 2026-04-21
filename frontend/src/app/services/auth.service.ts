import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, from, switchMap, tap } from 'rxjs';
import { Preferences } from '@capacitor/preferences';
import { environment } from '../../environments/environment';
import { User, AuthResponse, LoginRequest, RegisterRequest } from '../models/user.model';

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  private tokenSubject = new BehaviorSubject<string | null>(null);

  constructor(private http: HttpClient) {
    this.loadStoredAuth();
  }

  get currentUser(): User | null {
    return this.currentUserSubject.value;
  }

  get token(): string | null {
    return this.tokenSubject.value;
  }

  get isAuthenticated(): boolean {
    return !!this.tokenSubject.value;
  }

  private async loadStoredAuth(): Promise<void> {
    try {
      const tokenResult = await Preferences.get({ key: TOKEN_KEY });
      const userResult = await Preferences.get({ key: USER_KEY });

      if (tokenResult.value && userResult.value) {
        this.tokenSubject.next(tokenResult.value);
        this.currentUserSubject.next(JSON.parse(userResult.value));
      }
    } catch (e) {
      console.error('Error loading stored auth:', e);
    }
  }

  login(credentials: LoginRequest): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${environment.apiUrl}/auth/login`, credentials)
      .pipe(
        tap((response) => this.handleAuthResponse(response))
      );
  }

  register(data: RegisterRequest): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${environment.apiUrl}/auth/register`, data)
      .pipe(
        tap((response) => this.handleAuthResponse(response))
      );
  }

  getMe(): Observable<{ user: User }> {
    return this.http.get<{ user: User }>(`${environment.apiUrl}/auth/me`);
  }

  async logout(): Promise<void> {
    await Preferences.remove({ key: TOKEN_KEY });
    await Preferences.remove({ key: USER_KEY });
    this.tokenSubject.next(null);
    this.currentUserSubject.next(null);
  }

  private async handleAuthResponse(response: AuthResponse): Promise<void> {
    await Preferences.set({ key: TOKEN_KEY, value: response.access_token });
    await Preferences.set({ key: USER_KEY, value: JSON.stringify(response.user) });
    this.tokenSubject.next(response.access_token);
    this.currentUserSubject.next(response.user);
  }
}
