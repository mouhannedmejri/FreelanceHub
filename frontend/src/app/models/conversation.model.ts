import { User } from './user.model';
import { Offer } from './offer.model';

export interface Message {
  id: number | string;
  conversation_id: number | string;
  sender_id: number | string;
  content: string;
  is_read: boolean;
  created_at: string;
  delivered_to?: (number | string)[];
  read_by?: (number | string)[];
  reply_to_message_id?: number | string;
}

export interface Conversation {
  id: number | string;
  offer_id: number | string | null;
  last_message: string;
  last_message_at: string;
  participant_ids: (number | string)[];
  unread_counts?: Record<string, number>;
  offer?: Offer | null;
  other_user: User; // Added by frontend/backend helper
  unread_count: number; // Added by frontend/backend helper
}

export interface ConversationsResponse {
  conversations: Conversation[];
}

export interface MessagesResponse {
  messages: Message[];
  total: number;
  page: number;
  per_page: number;
}
