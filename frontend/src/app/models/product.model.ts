export interface Product {
  id: string;
  seller_id: string;
  seller_name: string;
  seller_avatar?: string;
  seller_rating?: number;
  seller_products_count?: number;
  title: string;
  description: string;
  category: string;
  main_category: string;
  sub_category: string;
  tags: string[];
  file_type: string;
  skills: string[];
  price: number;
  sale_price?: number | null;
  rating: number;
  review_count?: number;
  sales_count: number;
  download_count: number;
  view_count?: number;
  version: string;
  image_url: string;
  preview_images: string[];
  demo_url?: string;
  file_size: string;
  compatibility: string[];
  whats_included: string[];
  license_type: 'single' | 'multiple' | 'unlimited';
  is_featured: boolean;
  support_included: boolean;
  last_updated: string;
  created_at: string;
  reviews?: ProductReview[];
  related_products?: Product[];
}

export interface ProductReview {
  id: string;
  user_id: string;
  product_id: string;
  reviewer_name: string;
  rating: number;
  comment: string;
  created_at: string;
}

export interface Purchase {
  id: string;
  buyer_id: string;
  product_id: string;
  seller_id: string;
  amount: number;
  currency: string;
  status: string;
  download_token: string;
  download_count: number;
  download_limit: number;
  purchase_date: string;
  refund_eligible: boolean;
  refund_deadline: string;
  product?: Product;
  seller_name?: string;
}

export interface SellerAnalytics {
  total_products: number;
  total_views: number;
  total_downloads: number;
  total_sales: number;
  total_revenue: number;
  monthly_revenue: { month: string; revenue: number; sales: number }[];
  top_products: Product[];
  recent_sales: any[];
}

export interface ProductsResponse {
  data: Product[];
  meta: { page: number; total: number; has_more: boolean };
}

export interface ProductResponse {
  product: Product;
}
