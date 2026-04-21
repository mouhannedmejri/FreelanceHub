import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface HomeStats {
  freelancers: number;
  projects: number;
  clients: number;
}

@Injectable({
  providedIn: 'root',
})
export class HomeService {
  constructor(private http: HttpClient) {}

  getStats(): Observable<HomeStats> {
    return this.http.get<HomeStats>(`${environment.apiUrl}/home/stats`);
  }
}
