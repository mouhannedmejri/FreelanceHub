export interface Review {
  id?: number | string;
  target_user_id: number | string;
  reviewer_id?: number | string;
  rating: number;
  comment: string;
  created_at?: string;
  reviewer?: {
    id: number | string;
    full_name: string;
  };
}
