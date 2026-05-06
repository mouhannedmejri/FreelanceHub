import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { ProductService } from '../../services/product.service';
import { Product } from '../../models/product.model';
import { Subscription, Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { AuthService } from '../../services/auth.service';
import { GuestAccessService } from '../../services/guest-access.service';
import { ToastController, AlertController } from '@ionic/angular';

@Component({
  selector: 'app-digital-store',
  templateUrl: './digital-store.page.html',
  styleUrls: ['./digital-store.page.scss'],
  standalone: false
})
export class DigitalStorePage implements OnInit, OnDestroy {
  products: Product[] = [];
  featuredProducts: Product[] = [];
  isLoading = false;
  isLoadingFeatured = false;
  searchTerm = '';
  activeCategory = '';
  activeSort = 'recent';
  activeLicense = '';
  activeFileType = '';
  priceRange = { min: null as number | null, max: null as number | null };
  showFreeOnly = false;
  isFilterModalOpen = false;
  isProductDetailOpen = false;
  selectedProduct: Product | null = null;
  isPurchasing = false;
  activeImageIndex = 0;

  private searchSubject = new Subject<string>();
  private subs: Subscription[] = [];

  allProducts: Product[] = [];
  displayedProducts: Product[] = [];
  page = 1;
  pageSize = 10;
  hasMore = true;
  totalProducts = 0;

  categories = [
    { id: '', label: 'Tous', icon: 'apps-outline' },
    { id: 'website_templates', label: 'Sites Web', icon: 'globe-outline' },
    { id: 'mobile_app_templates', label: 'Apps Mobile', icon: 'phone-portrait-outline' },
    { id: 'design_assets', label: 'Design', icon: 'color-palette-outline' },
    { id: 'code_scripts', label: 'Scripts', icon: 'code-slash-outline' },
    { id: 'business_documents', label: 'Documents', icon: 'document-text-outline' }
  ];

  sortOptions = [
    { id: 'recent', label: 'Récents' },
    { id: 'popular', label: 'Populaires' },
    { id: 'price_low', label: 'Prix ↑' },
    { id: 'price_high', label: 'Prix ↓' },
    { id: 'rating', label: 'Mieux notés' }
  ];

  licenseTypes = [
    { id: '', label: 'Toutes' },
    { id: 'single', label: 'Single' },
    { id: 'multiple', label: 'Multiple' },
    { id: 'unlimited', label: 'Unlimited' }
  ];

  constructor(
    private productService: ProductService,
    private authService: AuthService,
    private guestAccessService: GuestAccessService,
    private toastController: ToastController,
    private alertController: AlertController,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadProducts();
    this.loadFeatured();

    this.subs.push(
      this.searchSubject.pipe(
        debounceTime(400),
        distinctUntilChanged()
      ).subscribe(() => {
        this.loadProducts();
      })
    );
  }

  ionViewWillEnter() {
    this.loadProducts();
  }

  ngOnDestroy() {
    this.subs.forEach(s => s.unsubscribe());
  }

  get isGuest(): boolean {
    return this.authService.isGuest;
  }

  get isFreelancer(): boolean {
    return this.authService.currentUser?.role === 'freelancer';
  }

  get activeFilterCount(): number {
    let c = 0;
    if (this.activeCategory) c++;
    if (this.activeLicense) c++;
    if (this.activeFileType) c++;
    if (this.priceRange.min !== null) c++;
    if (this.priceRange.max !== null) c++;
    if (this.showFreeOnly) c++;
    return c;
  }

  doRefresh(event: any) {
    this.loadProducts(event);
  }

  loadFeatured() {
    this.isLoadingFeatured = true;
    this.productService.getFeaturedProducts().subscribe({
      next: (res) => {
        this.featuredProducts = res.data || [];
        this.isLoadingFeatured = false;
      },
      error: () => { this.isLoadingFeatured = false; }
    });
  }

  loadProducts(event?: any) {
    if (this.isLoading && !event) return;
    this.isLoading = true;
    this.page = 1;

    const filters: any = {
      sort_by: this.activeSort
    };
    if (this.activeCategory) filters.main_category = this.activeCategory;
    if (this.searchTerm) filters.search = this.searchTerm;
    if (this.activeLicense) filters.license_type = this.activeLicense;
    if (this.activeFileType) filters.file_type = this.activeFileType;
    if (this.showFreeOnly) filters.is_free = 'true';
    if (this.priceRange.min !== null) filters.min_price = this.priceRange.min;
    if (this.priceRange.max !== null) filters.max_price = this.priceRange.max;

    this.productService.getProducts(filters).subscribe({
      next: (res) => {
        this.allProducts = res.data || [];
        this.totalProducts = res.meta?.total || this.allProducts.length;
        this.updateDisplayedProducts();
        this.isLoading = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoading = false;
        if (event) event.target.complete();
      }
    });
  }

  updateDisplayedProducts() {
    this.displayedProducts = this.allProducts.slice(0, this.page * this.pageSize);
    this.hasMore = this.displayedProducts.length < this.allProducts.length;
  }

  loadMore(event: any) {
    this.page++;
    this.updateDisplayedProducts();
    event.target.complete();
    if (!this.hasMore) event.target.disabled = true;
  }

  onSearch() {
    this.searchSubject.next(this.searchTerm);
  }

  filterByCategory(catId: string) {
    this.activeCategory = catId;
    this.loadProducts();
  }

  setSort(sortId: string) {
    this.activeSort = sortId;
    this.loadProducts();
  }

  openFilterModal() {
    this.isFilterModalOpen = true;
  }

  applyFilters() {
    this.isFilterModalOpen = false;
    this.loadProducts();
  }

  resetFilters() {
    this.activeCategory = '';
    this.activeLicense = '';
    this.activeFileType = '';
    this.priceRange = { min: null, max: null };
    this.showFreeOnly = false;
    this.applyFilters();
  }

  // ─── Product Detail ───────────────────────────────────────

  openProduct(product: Product) {
    this.selectedProduct = null;
    this.activeImageIndex = 0;
    this.productService.getProduct(product.id).subscribe({
      next: (res) => {
        this.selectedProduct = res.product;
        this.isProductDetailOpen = true;
      },
      error: () => {
        this.selectedProduct = product;
        this.isProductDetailOpen = true;
      }
    });
  }

  closeProductDetail() {
    this.isProductDetailOpen = false;
    this.selectedProduct = null;
  }

  setActiveImage(index: number) {
    this.activeImageIndex = index;
  }

  getProductImages(product: Product): string[] {
    const imgs = product.preview_images?.length ? product.preview_images : [];
    if (product.image_url && !imgs.includes(product.image_url)) {
      imgs.unshift(product.image_url);
    }
    return imgs.length ? imgs : ['assets/placeholder-product.png'];
  }

  getEffectivePrice(product: Product): number {
    return product.sale_price || product.price;
  }

  hasDiscount(product: Product): boolean {
    return !!(product.sale_price && product.sale_price < product.price);
  }

  getDiscountPercent(product: Product): number {
    if (!this.hasDiscount(product)) return 0;
    return Math.round((1 - (product.sale_price! / product.price)) * 100);
  }

  getLicenseLabel(type: string): string {
    switch (type) {
      case 'single': return 'Licence Unique';
      case 'multiple': return 'Multi-Licence';
      case 'unlimited': return 'Licence Illimitée';
      default: return type;
    }
  }

  getCategoryLabel(cat: string): string {
    const found = this.categories.find(c => c.id === cat);
    return found?.label || cat;
  }

  getCategoryIcon(cat: string): string {
    const found = this.categories.find(c => c.id === cat);
    return found?.icon || 'cube-outline';
  }

  formatFileSize(size: string): string {
    const bytes = parseInt(size, 10);
    if (isNaN(bytes) || bytes === 0) return 'N/A';
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    let s = bytes;
    while (s >= 1024 && i < units.length - 1) { s /= 1024; i++; }
    return `${s.toFixed(1)} ${units[i]}`;
  }

  // ─── Purchase ─────────────────────────────────────────────

  async buyProduct(product: Product) {
    if (this.isGuest) {
      this.guestAccessService.showSignupPrompt('Inscrivez-vous pour acheter des produits.');
      return;
    }

    if (product.price === 0) {
      this.confirmPurchase(product);
      return;
    }

    const alert = await this.alertController.create({
      header: 'Confirmer l\'achat',
      message: `Acheter "${product.title}" pour ${this.getEffectivePrice(product)}€ ?`,
      cssClass: 'dark-alert',
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        {
          text: 'Acheter maintenant',
          handler: () => this.confirmPurchase(product)
        }
      ]
    });
    await alert.present();
  }

  confirmPurchase(product: Product) {
    this.isPurchasing = true;
    this.productService.purchaseProduct(product.id).subscribe({
      next: async (res) => {
        this.isPurchasing = false;
        const toast = await this.toastController.create({
          message: '🎉 Achat réussi ! Accédez à "Mes Achats" pour télécharger.',
          duration: 4000, color: 'success'
        });
        toast.present();
        this.closeProductDetail();
        this.loadProducts();
      },
      error: async (err) => {
        this.isPurchasing = false;
        const msg = err.error?.error || 'Erreur lors de l\'achat';
        const toast = await this.toastController.create({
          message: msg, duration: 3000, color: 'danger'
        });
        toast.present();
      }
    });
  }

  openDemo(url: string) {
    if (url) window.open(url, '_blank');
  }

  navigateToSellerDashboard() {
    this.router.navigate(['/seller-dashboard']);
  }

  navigateToMyPurchases() {
    this.router.navigate(['/my-purchases']);
  }

  getStarArray(rating: number): number[] {
    return Array(5).fill(0).map((_, i) => i < Math.round(rating) ? 1 : 0);
  }
}
