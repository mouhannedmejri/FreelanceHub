import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { User } from '../models/user.model';

export interface AdminStats {
  total_users: number;
  freelancers: number;
  clients: number;
  offers: number;
  services: number;
  revenue: number;
}

@Injectable({ providedIn: 'root' })
export class AdminService {
  constructor(private http: HttpClient) {}

  getStats(): Observable<AdminStats> {
    return this.http.get<AdminStats>(`${environment.apiUrl}/admin/stats`);
  }

  getUsers(role?: string): Observable<{ users: User[] }> {
    let params = new HttpParams();
    if (role) params = params.set('role', role);
    return this.http.get<{ users: User[] }>(`${environment.apiUrl}/admin/users`, { params });
  }

  toggleApprove(userId: number): Observable<{ user: User }> {
    return this.http.patch<{ user: User }>(`${environment.apiUrl}/admin/users/${userId}/approve`, {});
  }
}
