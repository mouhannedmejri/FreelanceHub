export interface Service {
  id: number;
  freelancer_id: number;
  freelancer_name: string;
  title: string;
  description: string;
  category: string;
  cover_image_url: string;
  tags: string[];
  level: string;
  price_from: number;
  rating: number;
  review_count: number;
  created_at: string;
}

export interface PaginatedServices {
  services: Service[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}
