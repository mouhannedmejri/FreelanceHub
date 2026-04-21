import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Service, PaginatedServices } from '../models/service.model';

@Injectable({ providedIn: 'root' })
export class ServiceService {
  constructor(private http: HttpClient) {}

  getServices(params: {
    category?: string;
    search?: string;
    page?: number;
  }): Observable<PaginatedServices> {
    let httpParams = new HttpParams();
    if (params.category) {
      httpParams = httpParams.set('category', params.category);
    }
    if (params.search) {
      httpParams = httpParams.set('search', params.search);
    }
    if (params.page) {
      httpParams = httpParams.set('page', params.page.toString());
    }
    return this.http.get<PaginatedServices>(`${environment.apiUrl}/services`, {
      params: httpParams,
    });
  }

  getService(id: number): Observable<{ service: Service }> {
    return this.http.get<{ service: Service }>(
      `${environment.apiUrl}/services/${id}`
    );
  }
}
