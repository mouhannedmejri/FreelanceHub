import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { Notification, NotificationsResponse } from '../models/notification.model';

@Injectable({
  providedIn: 'root',
})
export class NotificationService {
  private unreadCountSubject = new BehaviorSubject<number>(0);
  public unreadCount$ = this.unreadCountSubject.asObservable();

  private notificationsSubject = new BehaviorSubject<Notification[]>([]);
  public notifications$ = this.notificationsSubject.asObservable();

  constructor(private http: HttpClient) {}

  get unreadCount(): number {
    return this.unreadCountSubject.value;
  }

  loadNotifications(): Observable<NotificationsResponse> {
    return this.http
      .get<NotificationsResponse>(`${environment.apiUrl}/notifications/`)
      .pipe(
        tap((res) => {
          this.notificationsSubject.next(res.notifications);
          this.unreadCountSubject.next(res.unread_count);
        })
      );
  }

  markAsRead(id: number): Observable<{ notification: Notification }> {
    return this.http
      .patch<{ notification: Notification }>(
        `${environment.apiUrl}/notifications/${id}/read`,
        {}
      )
      .pipe(
        tap(() => {
          const notifications = this.notificationsSubject.value.map((n) =>
            n.id === id ? { ...n, is_read: true } : n
          );
          this.notificationsSubject.next(notifications);
          this.unreadCountSubject.next(
            notifications.filter((n) => !n.is_read).length
          );
        })
      );
  }

  markAllAsRead(): Observable<{ message: string }> {
    return this.http
      .patch<{ message: string }>(
        `${environment.apiUrl}/notifications/read-all`,
        {}
      )
      .pipe(
        tap(() => {
          const notifications = this.notificationsSubject.value.map((n) => ({
            ...n,
            is_read: true,
          }));
          this.notificationsSubject.next(notifications);
          this.unreadCountSubject.next(0);
        })
      );
  }

  deleteNotification(id: number): Observable<{ message: string }> {
    return this.http
      .delete<{ message: string }>(
        `${environment.apiUrl}/notifications/${id}`
      )
      .pipe(
        tap(() => {
          const notifications = this.notificationsSubject.value.filter(
            (n) => n.id !== id
          );
          this.notificationsSubject.next(notifications);
          this.unreadCountSubject.next(
            notifications.filter((n) => !n.is_read).length
          );
        })
      );
  }
}
