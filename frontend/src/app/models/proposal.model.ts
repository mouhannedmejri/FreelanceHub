export interface Proposal {
  id: number;
  offer_id: number;
  freelancer_id: number;
  cover_letter: string;
  proposed_price: number;
  estimated_duration: string;
  status: 'pending' | 'accepted' | 'rejected';
  created_at: string;
  freelancer?: {
    id: number;
    full_name: string;
    email: string;
    role: string;
    is_approved: boolean;
  };
}
