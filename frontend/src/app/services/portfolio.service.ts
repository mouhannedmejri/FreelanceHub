import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class PortfolioService {
  constructor(private http: HttpClient) {}

  addProject(payload: any): Observable<any> {
    return this.http.post<any>(`${environment.apiUrl}/freelancer/portfolio/projects`, payload);
  }

  updateProject(projectId: string, payload: any): Observable<any> {
    return this.http.put<any>(`${environment.apiUrl}/freelancer/portfolio/projects/${projectId}`, payload);
  }

  deleteProject(projectId: string): Observable<any> {
    return this.http.delete<any>(`${environment.apiUrl}/freelancer/portfolio/projects/${projectId}`);
  }

  toggleFeatured(projectId: string): Observable<any> {
    return this.http.patch<any>(`${environment.apiUrl}/freelancer/portfolio/projects/${projectId}/feature`, {});
  }

  uploadProjectImages(projectId: string, files: File[]): Observable<any> {
    const formData = new FormData();
    files.forEach((f) => formData.append('images', f));
    return this.http.post<any>(`${environment.apiUrl}/freelancer/portfolio/projects/${projectId}/images`, formData);
  }
}

