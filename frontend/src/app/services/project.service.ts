import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  ProjectDetail,
  Milestone,
  Task,
  Deliverable,
  UpcomingMilestone
} from '../models/project.model';

@Injectable({ providedIn: 'root' })
export class ProjectService {
  private base = `${environment.apiUrl}/projects`;

  constructor(private http: HttpClient) {}

  // ── Project detail ──────────────────────────
  getProjectDetail(projectId: string): Observable<{ project: ProjectDetail }> {
    return this.http.get<{ project: ProjectDetail }>(`${this.base}/${projectId}/detail`);
  }

  // ── Milestones ──────────────────────────────
  createMilestone(projectId: string, payload: Partial<Milestone>): Observable<{ milestone: Milestone }> {
    return this.http.post<{ milestone: Milestone }>(`${this.base}/${projectId}/milestones`, payload);
  }

  updateMilestone(projectId: string, mid: string, payload: Partial<Milestone>): Observable<{ milestone: Milestone }> {
    return this.http.patch<{ milestone: Milestone }>(`${this.base}/${projectId}/milestones/${mid}`, payload);
  }

  // ── Tasks ───────────────────────────────────
  createTask(projectId: string, payload: Partial<Task>): Observable<{ task: Task; progress_percent: number }> {
    return this.http.post<{ task: Task; progress_percent: number }>(`${this.base}/${projectId}/tasks`, payload);
  }

  updateTask(projectId: string, tid: string, payload: Partial<Task>): Observable<{ task: Task; progress_percent: number }> {
    return this.http.patch<{ task: Task; progress_percent: number }>(`${this.base}/${projectId}/tasks/${tid}`, payload);
  }

  deleteTask(projectId: string, tid: string): Observable<{ message: string; progress_percent: number }> {
    return this.http.delete<{ message: string; progress_percent: number }>(`${this.base}/${projectId}/tasks/${tid}`);
  }

  // ── Progress ────────────────────────────────
  getProgress(projectId: string): Observable<any> {
    return this.http.get<any>(`${this.base}/${projectId}/progress`);
  }

  // ── Deliverables ────────────────────────────
  getDeliverables(projectId: string): Observable<{ deliverables: Deliverable[] }> {
    return this.http.get<{ deliverables: Deliverable[] }>(`${this.base}/${projectId}/deliverables`);
  }

  addDeliverable(projectId: string, payload: { milestone_id?: string; file_url: string; file_name?: string }): Observable<{ deliverable: Deliverable }> {
    return this.http.post<{ deliverable: Deliverable }>(`${this.base}/${projectId}/deliverables`, payload);
  }

  confirmDeliverable(projectId: string, did: string): Observable<any> {
    return this.http.patch<any>(`${this.base}/${projectId}/deliverables/${did}/confirm`, {});
  }

  // ── Budget ──────────────────────────────────
  updateBudget(projectId: string, payload: { total_budget?: number; paid_amount?: number }): Observable<any> {
    return this.http.patch<any>(`${this.base}/${projectId}/budget`, payload);
  }

  // ── Upcoming milestones (home widget) ───────
  getUpcomingMilestones(): Observable<{ milestones: UpcomingMilestone[] }> {
    return this.http.get<{ milestones: UpcomingMilestone[] }>(`${this.base}/upcoming-milestones`);
  }
}
