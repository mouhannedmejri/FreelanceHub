export interface Product {
  id: number;
  seller_id: number;
  seller_name: string;
  title: string;
  description: string;
  category: string;
  skills: string[];
  price: number;
  rating: number;
  sales_count: number;
  version: string;
  image_url: string;
  created_at: string;
}

export interface ProductsResponse {
  products: Product[];
}

export interface ProductResponse {
  product: Product;
}
