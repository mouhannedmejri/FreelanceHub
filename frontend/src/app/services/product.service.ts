import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  Product, ProductsResponse, ProductResponse,
  Purchase, SellerAnalytics, ProductReview
} from '../models/product.model';

@Injectable({ providedIn: 'root' })
export class ProductService {
  private base = `${environment.apiUrl}/store`;

  constructor(private http: HttpClient) {}

  // ─── Public Browsing ──────────────────────────────────────

  getProducts(filters: any = {}): Observable<ProductsResponse> {
    let params = new HttpParams();
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
        params = params.set(key, filters[key]);
      }
    });
    return this.http.get<ProductsResponse>(`${this.base}/products`, { params });
  }

  getFeaturedProducts(): Observable<{ data: Product[] }> {
    return this.http.get<{ data: Product[] }>(`${this.base}/products/featured`);
  }

  getCategories(): Observable<{ categories: { id: string; count: number }[] }> {
    return this.http.get<{ categories: { id: string; count: number }[] }>(`${this.base}/products/categories`);
  }

  getProduct(id: string): Observable<ProductResponse> {
    return this.http.get<ProductResponse>(`${this.base}/products/${id}`);
  }

  // ─── Seller Management ────────────────────────────────────

  createProduct(formData: FormData): Observable<ProductResponse> {
    return this.http.post<ProductResponse>(`${this.base}/products`, formData);
  }

  updateProduct(id: string, data: Partial<Product>): Observable<ProductResponse> {
    return this.http.put<ProductResponse>(`${this.base}/products/${id}`, data);
  }

  deleteProduct(id: string): Observable<any> {
    return this.http.delete(`${this.base}/products/${id}`);
  }

  getSellerProducts(): Observable<{ data: Product[] }> {
    return this.http.get<{ data: Product[] }>(`${this.base}/seller/products`);
  }

  getSellerAnalytics(): Observable<SellerAnalytics> {
    return this.http.get<SellerAnalytics>(`${this.base}/seller/analytics`);
  }

  // ─── Purchases ────────────────────────────────────────────

  purchaseProduct(productId: string): Observable<{ purchase: Purchase; download_token: string }> {
    return this.http.post<{ purchase: Purchase; download_token: string }>(
      `${this.base}/products/${productId}/purchase`, {}
    );
  }

  getMyPurchases(): Observable<{ data: Purchase[] }> {
    return this.http.get<{ data: Purchase[] }>(`${this.base}/purchases`);
  }

  downloadPurchase(purchaseId: string): Observable<any> {
    return this.http.get(`${this.base}/purchases/${purchaseId}/download`, { responseType: 'blob' as 'json' });
  }

  requestRefund(purchaseId: string, reason: string): Observable<any> {
    return this.http.post(`${this.base}/purchases/${purchaseId}/refund`, { reason });
  }

  // ─── Reviews ──────────────────────────────────────────────

  getProductReviews(productId: string): Observable<{ data: ProductReview[] }> {
    return this.http.get<{ data: ProductReview[] }>(`${this.base}/products/${productId}/reviews`);
  }

  submitReview(productId: string, rating: number, comment: string): Observable<any> {
    return this.http.post(`${this.base}/products/${productId}/reviews`, { rating, comment });
  }
}
