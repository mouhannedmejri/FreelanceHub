import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { User } from '../models/user.model';

export interface AdminStats {
  total_users: number;
  freelancers_count: number;
  clients_count: number;
  admins_count: number;
  pending_approvals: number;
  open_claims: number;
  active_projects: number;
  completed_projects: number;
  total_revenue: number;
  new_users_this_month: number;
  new_users_last_month: number;
  revenue_this_month: number;
  revenue_last_month: number;
  recent_activity: any[];
}

@Injectable({ providedIn: 'root' })
export class AdminService {
  constructor(private http: HttpClient) {}

  getStats(): Observable<AdminStats> {
    return this.http.get<AdminStats>(`${environment.apiUrl}/admin/stats`);
  }

  getApprovalCounts(): Observable<{ pending: number, approved: number, rejected: number }> {
    return this.http.get<{ pending: number, approved: number, rejected: number }>(`${environment.apiUrl}/admin/approvals/counts`);
  }

  getApprovals(type?: string, status: string = 'pending', page: number = 1, perPage: number = 10): Observable<any> {
    let params = new HttpParams()
      .set('status', status)
      .set('page', page.toString())
      .set('per_page', perPage.toString());
    if (type) params = params.set('type', type);
    return this.http.get<any>(`${environment.apiUrl}/admin/approvals`, { params });
  }

  updateApproval(appId: string, status: 'approved' | 'rejected', adminNote?: string): Observable<any> {
    return this.http.patch<any>(`${environment.apiUrl}/admin/approvals/${appId}`, { status, admin_note: adminNote });
  }

  getUsers(role?: string, status?: string, search?: string, page: number = 1, perPage: number = 15): Observable<any> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('per_page', perPage.toString());
    if (role && role !== 'all') params = params.set('role', role);
    if (status && status !== 'all') params = params.set('status', status);
    if (search) params = params.set('search', search);
    return this.http.get<any>(`${environment.apiUrl}/admin/users`, { params });
  }

  getUserDetails(userId: string): Observable<any> {
    return this.http.get<any>(`${environment.apiUrl}/admin/users/${userId}/details`);
  }

  toggleApprove(userId: string): Observable<{ user: User }> {
    return this.http.patch<{ user: User }>(`${environment.apiUrl}/admin/users/${userId}/approve`, {});
  }

  banUser(userId: string, reason: string, expiresAt: string | null): Observable<any> {
    return this.http.patch<any>(`${environment.apiUrl}/admin/users/${userId}/ban`, { reason, expires_at: expiresAt });
  }

  unbanUser(userId: string): Observable<any> {
    return this.http.patch<any>(`${environment.apiUrl}/admin/users/${userId}/unban`, {});
  }

  deleteUser(userId: string): Observable<any> {
    return this.http.delete<any>(`${environment.apiUrl}/admin/users/${userId}`);
  }

  getClaims(status?: string, priority?: string, type?: string, page: number = 1, perPage: number = 10): Observable<any> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('per_page', perPage.toString());
    if (status && status !== 'all') params = params.set('status', status);
    if (priority && priority !== 'all') params = params.set('priority', priority);
    if (type && type !== 'all') params = params.set('type', type);
    return this.http.get<any>(`${environment.apiUrl}/admin/claims`, { params });
  }

  updateClaim(claimId: string, status?: string, adminNote?: string, priority?: string): Observable<any> {
    return this.http.patch<any>(`${environment.apiUrl}/admin/claims/${claimId}`, { status, admin_note: adminNote, priority });
  }
}
