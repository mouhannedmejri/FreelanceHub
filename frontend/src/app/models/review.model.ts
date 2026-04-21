export interface Review {
  id: number;
  reviewer_id: number;
  target_id: number;
  rating: number;
  comment: string;
  created_at: string;
  reviewer?: {
    id: number;
    full_name: string;
  };
}
