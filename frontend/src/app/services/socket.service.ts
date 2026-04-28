import { Injectable } from '@angular/core';
import { BehaviorSubject, Subject } from 'rxjs';
import { io, Socket } from 'socket.io-client';
import { environment } from '../../environments/environment';

type TypingEvent = {
  conversation_id: string;
  user_id: string;
  is_typing: boolean;
};

@Injectable({ providedIn: 'root' })
export class SocketService {
  private socket: Socket | null = null;
  private typingTimers = new Map<string, ReturnType<typeof setTimeout>>();
  private typingDebounceTimers = new Map<string, ReturnType<typeof setTimeout>>();

  private onlineUsersSubject = new BehaviorSubject<Set<string>>(new Set());
  onlineUsers$ = this.onlineUsersSubject.asObservable();

  private messageNewSubject = new Subject<any>();
  messageNew$ = this.messageNewSubject.asObservable();

  private messageReadSubject = new Subject<any>();
  messageRead$ = this.messageReadSubject.asObservable();

  private messageDeliveredSubject = new Subject<any>();
  messageDelivered$ = this.messageDeliveredSubject.asObservable();

  private typingSubject = new Subject<TypingEvent>();
  typing$ = this.typingSubject.asObservable();

  connect(token: string): void {
    if (!token) return;
    if (this.socket?.connected) return;

    const socketBaseUrl = environment.apiUrl.replace(/\/api\/?$/, '');
    this.socket = io(socketBaseUrl, {
      transports: ['websocket'],
      auth: { token },
    });

    this.socket.on('message:new', (payload) => this.messageNewSubject.next(payload));
    this.socket.on('message:read', (payload) => this.messageReadSubject.next(payload));
    this.socket.on('message:delivered', (payload) => this.messageDeliveredSubject.next(payload));
    this.socket.on('user:typing', (payload: TypingEvent) => this.typingSubject.next(payload));
    this.socket.on('user:online', (payload: { user_id: string; online: boolean }) => {
      const next = new Set(this.onlineUsersSubject.value);
      if (payload.online) {
        next.add(payload.user_id);
      } else {
        next.delete(payload.user_id);
      }
      this.onlineUsersSubject.next(next);
    });
  }

  disconnect(): void {
    this.socket?.disconnect();
    this.socket = null;
    this.onlineUsersSubject.next(new Set());
  }

  emitTyping(conversationId: string, userId: string): void {
    if (!this.socket) return;
    const key = `${conversationId}:${userId}`;

    const emitTypingNow = () => {
      this.socket?.emit('user:typing', {
        conversation_id: conversationId,
        user_id: userId,
        is_typing: true,
      });
      const existingStop = this.typingTimers.get(key);
      if (existingStop) clearTimeout(existingStop);
      const stopTimer = setTimeout(() => {
        this.socket?.emit('user:typing', {
          conversation_id: conversationId,
          user_id: userId,
          is_typing: false,
        });
      }, 1200);
      this.typingTimers.set(key, stopTimer);
    };

    const existingDebounce = this.typingDebounceTimers.get(key);
    if (existingDebounce) clearTimeout(existingDebounce);
    const debounceTimer = setTimeout(emitTypingNow, 200);
    this.typingDebounceTimers.set(key, debounceTimer);
  }
}
