import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, BehaviorSubject, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { Conversation, ConversationsResponse, MessagesResponse, Message } from '../models/conversation.model';

@Injectable({ providedIn: 'root' })
export class ConversationService {
  private unreadCountSubject = new BehaviorSubject<number>(0);
  public unreadCount$ = this.unreadCountSubject.asObservable();

  constructor(private http: HttpClient) {}

  getConversations(search?: string): Observable<ConversationsResponse> {
    let params = new HttpParams();
    if (search) {
      params = params.set('search', search);
    }
    return this.http.get<ConversationsResponse>(`${environment.apiUrl}/conversations/`, { params }).pipe(
      tap(res => {
        const totalUnread = res.conversations.reduce((acc, curr) => acc + curr.unread_count, 0);
        this.unreadCountSubject.next(totalUnread);
      })
    );
  }

  getMessages(conversationId: number, page: number = 1, perPage: number = 50): Observable<MessagesResponse> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('per_page', perPage.toString());
    return this.http.get<MessagesResponse>(`${environment.apiUrl}/conversations/${conversationId}/messages`, { params });
  }

  startConversation(payload: { user_id?: number, offer_id?: number }): Observable<{ conversation: Conversation }> {
    return this.http.post<{ conversation: Conversation }>(`${environment.apiUrl}/conversations/`, payload);
  }

  sendMessage(conversationId: number, content: string): Observable<{ message: Message }> {
    return this.http.post<{ message: Message }>(`${environment.apiUrl}/conversations/${conversationId}/messages`, { content });
  }

  updateUnreadCount(count: number) {
    this.unreadCountSubject.next(count);
  }
}
