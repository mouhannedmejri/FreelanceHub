import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Proposal } from '../models/proposal.model';

@Injectable({ providedIn: 'root' })
export class ProposalService {
  constructor(private http: HttpClient) {}

  submitProposal(offerId: number, data: Partial<Proposal>): Observable<{ proposal: Proposal }> {
    return this.http.post<{ proposal: Proposal }>(`${environment.apiUrl}/offers/${offerId}/proposals`, data);
  }

  getOfferProposals(offerId: number): Observable<{ proposals: Proposal[] }> {
    return this.http.get<{ proposals: Proposal[] }>(`${environment.apiUrl}/offers/${offerId}/proposals`);
  }

  updateProposalStatus(proposalId: number, status: 'accepted' | 'rejected'): Observable<{ proposal: Proposal }> {
    return this.http.patch<{ proposal: Proposal }>(`${environment.apiUrl}/proposals/${proposalId}`, { status });
  }

  updateProposal(proposalId: number, status: 'accepted' | 'rejected') {
    return this.http.patch(`${environment.apiUrl}/proposals/${proposalId}`, { status });
  }
}
