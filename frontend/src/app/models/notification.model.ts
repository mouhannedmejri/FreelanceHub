export interface Notification {
  id: number;
  user_id: number;
  type: 'message' | 'offre' | 'paiement' | 'avis' | 'offer' | 'payment' | 'review';
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
}

export interface NotificationsResponse {
  notifications: Notification[];
  unread_count: number;
}
