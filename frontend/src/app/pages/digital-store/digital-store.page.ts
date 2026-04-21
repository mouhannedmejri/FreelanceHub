import { Component, OnInit, OnDestroy } from '@angular/core';
import { ProductService } from '../../services/product.service';
import { Product } from '../../models/product.model';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-digital-store',
  templateUrl: './digital-store.page.html',
  styleUrls: ['./digital-store.page.scss'],
  standalone: false
})
export class DigitalStorePage implements OnInit, OnDestroy {
  products: Product[] = [];
  filteredProducts: Product[] = [];
  isLoading = false;
  searchTerm = '';
  activeCategory = '';
  private searchTimeout: any;
  private subs: Subscription[] = [];

  categories = [
    { id: '', label: 'Tous', icon: 'apps-outline' },
    { id: 'starter-kit', label: 'Starter Kits', icon: 'rocket-outline' },
    { id: 'ui-kit', label: 'UI Kits', icon: 'color-palette-outline' },
    { id: 'template', label: 'Templates', icon: 'desktop-outline' },
    { id: 'plan-archi', label: 'Plans Archi', icon: 'home-outline' }
  ];

  constructor(private productService: ProductService) {}

  ngOnInit() {
    this.loadProducts();
  }

  ngOnDestroy() {
    this.subs.forEach((s) => s.unsubscribe());
  }

  loadProducts() {
    this.isLoading = true;
    this.subs.push(
      this.productService.getProducts(this.activeCategory, this.searchTerm).subscribe({
        next: (res) => {
          this.products = res.products;
          this.filteredProducts = res.products;
          this.isLoading = false;
        },
        error: () => {
          this.isLoading = false;
        }
      })
    );
  }

  onSearch() {
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(() => {
      this.loadProducts();
    }, 300);
  }

  filterByCategory(catId: string) {
    this.activeCategory = catId;
    this.loadProducts();
  }
}
