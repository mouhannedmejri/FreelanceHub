import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, BehaviorSubject, tap, map, catchError, of } from 'rxjs';
import { environment } from '../../environments/environment';
import { Conversation, ConversationsResponse, MessagesResponse, Message } from '../models/conversation.model';
import { SocketService } from './socket.service';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class ConversationService {
  private unreadCountSubject = new BehaviorSubject<number>(0);
  public unreadCount$ = this.unreadCountSubject.asObservable();

  constructor(
    private http: HttpClient,
    private socketService: SocketService,
    private authService: AuthService
  ) {
    this.socketService.messageNew$.subscribe((payload: { conversation_id: string; message: Message }) => {
      if (!payload?.message) return;
      if (String(payload.message.sender_id) === String(this.authService.currentUser?.id)) return;
      this.unreadCountSubject.next(this.unreadCountSubject.value + 1);
    });
    this.socketService.messageRead$.subscribe(() => {
      if (this.unreadCountSubject.value > 0) {
        this.unreadCountSubject.next(this.unreadCountSubject.value - 1);
      }
    });
  }

  getConversations(search?: string): Observable<ConversationsResponse> {
    let params = new HttpParams();
    if (search) {
      params = params.set('search', search);
    }
    return this.http.get<ConversationsResponse>(`${environment.apiUrl}/conversations/`, { params }).pipe(
      tap(res => {
        const convs = res?.conversations || [];
        const totalUnread = convs.reduce((acc, curr) => acc + (curr.unread_count || 0), 0);
        this.unreadCountSubject.next(totalUnread);
      })
    );
  }

  getMessages(conversationId: number | string, page: number = 1, perPage: number = 50): Observable<MessagesResponse> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('per_page', perPage.toString());
    return this.http.get<any>(`${environment.apiUrl}/conversations/${conversationId}/messages`, { params }).pipe(
      map(res => {
        // Defensively handle multiple possible response shapes
        const messages: Message[] = res?.messages || res?.data || (Array.isArray(res) ? res : []);
        return {
          messages,
          total: res?.total || messages.length,
          page: res?.page || page,
          per_page: res?.per_page || perPage,
        } as MessagesResponse;
      }),
      catchError(err => {
        console.error('Failed to load messages:', err);
        return of({ messages: [], total: 0, page, per_page: perPage } as MessagesResponse);
      })
    );
  }

  startConversation(payload: { user_id?: number | string, offer_id?: number | string }): Observable<{ conversation: Conversation }> {
    return this.http.post<{ conversation: Conversation }>(`${environment.apiUrl}/conversations/`, payload);
  }

  sendMessage(
    conversationId: number | string,
    content: string,
    reply_to_message_id?: number | string
  ): Observable<{ message: Message }> {
    return this.http.post<{ message: Message }>(
      `${environment.apiUrl}/conversations/${conversationId}/messages`,
      { content, reply_to_message_id }
    );
  }

  markConversationRead(conversationId: number | string): Observable<{ ok: boolean; read_count: number }> {
    return this.http.post<{ ok: boolean; read_count: number }>(
      `${environment.apiUrl}/conversations/${conversationId}/read`,
      {}
    );
  }

  updateUnreadCount(count: number) {
    this.unreadCountSubject.next(count);
  }
}
