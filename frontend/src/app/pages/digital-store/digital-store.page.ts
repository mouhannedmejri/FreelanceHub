import { Component, OnInit, OnDestroy } from '@angular/core';
import { ProductService } from '../../services/product.service';
import { Product } from '../../models/product.model';
import { Subscription } from 'rxjs';
import { AuthService } from '../../services/auth.service';
import { GuestAccessService } from '../../services/guest-access.service';

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

  allProducts: Product[] = [];
  displayedProducts: Product[] = [];
  page = 1;
  pageSize = 10;
  hasMore = true;

  constructor(
    private productService: ProductService,
    private authService: AuthService,
    private guestAccessService: GuestAccessService
  ) {}

  ngOnInit() {
    this.loadProducts();
  }

  ngOnDestroy() {
    this.subs.forEach((s) => s.unsubscribe());
  }

  doRefresh(event: any) {
    this.loadProducts(event);
  }

  loadProducts(event?: any) {
    if (this.isLoading && !event) return;
    this.isLoading = true;
    this.page = 1;
    
    this.subs.push(
      this.productService.getProducts(this.activeCategory, this.searchTerm).subscribe({
        next: (res) => {
          this.allProducts = res.products;
          this.filteredProducts = res.products;
          this.updateDisplayedProducts();
          this.isLoading = false;
          if (event) event.target.complete();
        },
        error: () => {
          this.isLoading = false;
          if (event) event.target.complete();
        }
      })
    );
  }

  updateDisplayedProducts() {
    this.displayedProducts = this.filteredProducts.slice(0, this.page * this.pageSize);
    this.hasMore = this.displayedProducts.length < this.filteredProducts.length;
  }

  loadMore(event: any) {
    this.page++;
    this.updateDisplayedProducts();
    event.target.complete();
    if (!this.hasMore) {
      event.target.disabled = true;
    }
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

  get isGuest(): boolean {
    return this.authService.isGuest;
  }

  onBuyClick() {
    this.guestAccessService.showSignupPrompt('Sign up to purchase products.');
  }
}
