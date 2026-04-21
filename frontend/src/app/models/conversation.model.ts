import { User } from './user.model';
import { Offer } from './offer.model';

export interface Message {
  id: number;
  conversation_id: number;
  sender_id: number;
  content: string;
  is_read: boolean;
  created_at: string;
}

export interface Conversation {
  id: number;
  participant_1_id: number;
  participant_2_id: number;
  offer_id: number | null;
  last_message: string;
  last_message_at: string;
  unread_count_p1: number;
  unread_count_p2: number;
  created_at: string;
  participant_1: User;
  participant_2: User;
  offer: Offer | null;
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
