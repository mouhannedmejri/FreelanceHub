import { Component, OnInit } from '@angular/core';
import { ProductService } from '../../services/product.service';
import { Purchase } from '../../models/product.model';
import { ToastController, AlertController, ModalController } from '@ionic/angular';
import { LeaveReviewComponent } from '../../components/leave-review/leave-review.component';

@Component({
  selector: 'app-my-purchases',
  templateUrl: './my-purchases.page.html',
  styleUrls: ['./my-purchases.page.scss'],
  standalone: false
})
export class MyPurchasesPage implements OnInit {
  purchases: Purchase[] = [];
  isLoading = true;

  constructor(
    private productService: ProductService,
    private toastController: ToastController,
    private alertController: AlertController,
    private modalCtrl: ModalController
  ) {}

  ngOnInit() {
    this.loadPurchases();
  }

  loadPurchases(event?: any) {
    this.productService.getMyPurchases().subscribe({
      next: (res) => {
        this.purchases = res.data || [];
        this.isLoading = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoading = false;
        if (event) event.target.complete();
      }
    });
  }

  downloadProduct(purchase: Purchase) {
    if (purchase.download_count >= purchase.download_limit) {
      this.toastController.create({
        message: 'Limite de téléchargement atteinte.',
        duration: 3000, color: 'danger'
      }).then(t => t.present());
      return;
    }

    // Call API to get file or trigger download
    this.productService.downloadPurchase(purchase.id).subscribe({
      next: (blob) => {
        // Create link to download blob
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = purchase.product?.title || 'download';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        
        purchase.download_count++; // Local update
        this.toastController.create({
          message: 'Téléchargement démarré.',
          duration: 2000, color: 'success'
        }).then(t => t.present());
      },
      error: async (err) => {
        const toast = await this.toastController.create({
          message: err.error?.error || 'Erreur lors du téléchargement.',
          duration: 3000, color: 'danger'
        });
        toast.present();
      }
    });
  }

  async requestRefund(purchase: Purchase) {
    const alert = await this.alertController.create({
      header: 'Demander un remboursement',
      message: 'Veuillez expliquer la raison du remboursement :',
      inputs: [
        {
          name: 'reason',
          type: 'textarea',
          placeholder: 'Le produit ne correspond pas à la description...'
        }
      ],
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        {
          text: 'Envoyer',
          handler: (data) => {
            if (!data.reason) return false;
            this.productService.requestRefund(purchase.id, data.reason).subscribe({
              next: () => {
                purchase.status = 'refund_requested';
                this.toastController.create({
                  message: 'Demande de remboursement envoyée.',
                  duration: 3000, color: 'success'
                }).then(t => t.present());
              },
              error: (err) => {
                this.toastController.create({
                  message: err.error?.error || 'Erreur lors de la demande.',
                  duration: 3000, color: 'danger'
                }).then(t => t.present());
              }
            });
            return true;
          }
        }
      ]
    });
    await alert.present();
  }

  async leaveReview(purchase: Purchase) {
    const modal = await this.modalCtrl.create({
      component: LeaveReviewComponent,
      cssClass: 'review-modal-overlay',
      componentProps: {
        product: purchase.product
      }
    });
    await modal.present();
    const { data } = await modal.onDidDismiss();
    
    if (data?.rating) {
      this.productService.submitReview(purchase.product_id, data.rating, data.comment).subscribe({
        next: () => {
          this.toastController.create({
            message: 'Avis publié avec succès.',
            duration: 3000, color: 'success'
          }).then(t => t.present());
        },
        error: (err) => {
          this.toastController.create({
            message: err.error?.error || 'Erreur lors de la publication de l\'avis.',
            duration: 3000, color: 'danger'
          }).then(t => t.present());
        }
      });
    }
  }

  getStatusColor(status: string): string {
    switch (status) {
      case 'completed': return 'success';
      case 'refund_requested': return 'warning';
      case 'refunded': return 'danger';
      default: return 'medium';
    }
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'completed': return 'Complété';
      case 'refund_requested': return 'Remboursement demandé';
      case 'refunded': return 'Remboursé';
      default: return status;
    }
  }

  isRefundEligible(purchase: Purchase): boolean {
    if (purchase.status !== 'completed') return false;
    const now = new Date();
    const deadline = new Date(purchase.refund_deadline);
    return now <= deadline;
  }
}
