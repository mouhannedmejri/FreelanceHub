import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Product, ProductsResponse, ProductResponse } from '../models/product.model';

@Injectable({ providedIn: 'root' })
export class ProductService {
  constructor(private http: HttpClient) {}

  getProducts(category?: string, search?: string): Observable<ProductsResponse> {
    let params = new HttpParams();
    if (category) {
      params = params.set('category', category);
    }
    if (search) {
      params = params.set('search', search);
    }
    return this.http.get<ProductsResponse>(`${environment.apiUrl}/store/products`, { params });
  }

  getProduct(id: number): Observable<ProductResponse> {
    return this.http.get<ProductResponse>(`${environment.apiUrl}/store/products/${id}`);
  }

  createProduct(productData: Partial<Product>): Observable<ProductResponse> {
    return this.http.post<ProductResponse>(`${environment.apiUrl}/store/products`, productData);
  }
}
