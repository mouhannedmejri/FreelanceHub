import { Component, OnInit } from '@angular/core';
import { ProductService } from '../../services/product.service';
import { Product, SellerAnalytics } from '../../models/product.model';
import { ToastController, AlertController } from '@ionic/angular';

@Component({
  selector: 'app-seller-dashboard',
  templateUrl: './seller-dashboard.page.html',
  styleUrls: ['./seller-dashboard.page.scss'],
  standalone: false
})
export class SellerDashboardPage implements OnInit {
  analytics: SellerAnalytics | null = null;
  products: Product[] = [];
  isLoading = false;
  activeSegment = 'overview'; // overview, products, add

  // Form for new product
  newProduct: any = {
    title: '',
    description: '',
    main_category: '',
    price: 0,
    license_type: 'single',
    support_included: false
  };
  productFile: File | null = null;
  previewImages: File[] = [];

  categories = [
    { id: 'website_templates', label: 'Sites Web' },
    { id: 'mobile_app_templates', label: 'Apps Mobile' },
    { id: 'design_assets', label: 'Design' },
    { id: 'code_scripts', label: 'Scripts' },
    { id: 'business_documents', label: 'Documents' }
  ];

  constructor(
    private productService: ProductService,
    private toastController: ToastController,
    private alertController: AlertController
  ) {}

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.isLoading = true;
    this.productService.getSellerAnalytics().subscribe({
      next: (res) => {
        this.analytics = res;
        this.loadProducts();
      },
      error: () => {
        this.isLoading = false;
      }
    });
  }

  loadProducts() {
    this.productService.getSellerProducts().subscribe({
      next: (res) => {
        this.products = res.data || [];
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      }
    });
  }

  doRefresh(event: any) {
    this.loadData();
    setTimeout(() => {
      event.target.complete();
    }, 1000);
  }

  segmentChanged(event: any) {
    this.activeSegment = event.detail.value;
  }

  onFileSelected(event: any, type: 'product' | 'preview') {
    const files = event.target.files;
    if (files && files.length > 0) {
      if (type === 'product') {
        this.productFile = files[0];
      } else {
        for (let i = 0; i < files.length; i++) {
          this.previewImages.push(files[i]);
        }
      }
    }
  }

  removePreviewImage(index: number) {
    this.previewImages.splice(index, 1);
  }

  async submitProduct() {
    if (!this.newProduct.title || !this.newProduct.main_category || !this.newProduct.description) {
      const toast = await this.toastController.create({
        message: 'Veuillez remplir les champs obligatoires.',
        duration: 3000, color: 'warning'
      });
      toast.present();
      return;
    }

    if (!this.productFile) {
      const toast = await this.toastController.create({
        message: 'Le fichier du produit est requis.',
        duration: 3000, color: 'warning'
      });
      toast.present();
      return;
    }

    this.isLoading = true;
    const formData = new FormData();
    formData.append('title', this.newProduct.title);
    formData.append('description', this.newProduct.description);
    formData.append('category', this.newProduct.main_category); // legacy fallback
    formData.append('main_category', this.newProduct.main_category);
    formData.append('price', this.newProduct.price.toString());
    formData.append('license_type', this.newProduct.license_type);
    formData.append('support_included', this.newProduct.support_included ? 'true' : 'false');
    
    formData.append('product_file', this.productFile);
    
    this.previewImages.forEach((file, index) => {
      formData.append(`preview_image_${index}`, file);
    });

    this.productService.createProduct(formData).subscribe({
      next: async (res) => {
        this.isLoading = false;
        const toast = await this.toastController.create({
          message: 'Produit publié avec succès !',
          duration: 3000, color: 'success'
        });
        toast.present();
        this.resetForm();
        this.loadData();
        this.activeSegment = 'products';
      },
      error: async (err) => {
        this.isLoading = false;
        const toast = await this.toastController.create({
          message: 'Erreur lors de la publication.',
          duration: 3000, color: 'danger'
        });
        toast.present();
      }
    });
  }

  resetForm() {
    this.newProduct = {
      title: '', description: '', main_category: '', price: 0,
      license_type: 'single', support_included: false
    };
    this.productFile = null;
    this.previewImages = [];
  }

  async deleteProduct(product: Product) {
    const alert = await this.alertController.create({
      header: 'Confirmer',
      message: `Supprimer "${product.title}" ?`,
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        { 
          text: 'Supprimer',
          role: 'destructive',
          handler: () => {
            this.productService.deleteProduct(product.id).subscribe(() => {
              this.loadProducts();
              this.toastController.create({
                message: 'Produit supprimé', duration: 2000, color: 'success'
              }).then(t => t.present());
            });
          }
        }
      ]
    });
    await alert.present();
  }
}
