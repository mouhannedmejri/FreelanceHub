import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ClientService {
  constructor(private http: HttpClient) {}

  getDashboard(): Observable<any> {
    return this.http.get<any>(`${environment.apiUrl}/client/dashboard`);
  }

  getProjects(status: string = 'all', page: number = 1, perPage: number = 10): Observable<any> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('per_page', perPage.toString());
    
    if (status !== 'all') {
      params = params.set('status', status);
    }
    
    return this.http.get<any>(`${environment.apiUrl}/client/projects`, { params });
  }

  getProjectDetails(projectId: string): Observable<any> {
    return this.http.get<any>(`${environment.apiUrl}/client/projects/${projectId}`);
  }
}
