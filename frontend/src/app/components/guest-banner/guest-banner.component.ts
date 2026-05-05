import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ModalController } from '@ionic/angular';
import { AuthService } from '../../services/auth.service';
import { AuthModalComponent } from '../auth-modal/auth-modal.component';

@Component({
  selector: 'app-guest-banner',
  templateUrl: './guest-banner.component.html',
  styleUrls: ['./guest-banner.component.scss'],
  standalone: false,
})
export class GuestBannerComponent {
  dismissed = false;

  constructor(
    private authService: AuthService,
    private modalCtrl: ModalController,
    private router: Router
  ) {}

  get visible(): boolean {
    return !this.dismissed && !this.authService.isAuthenticated;
  }

  async openSignUp() {
    const modal = await this.modalCtrl.create({
      component: AuthModalComponent,
      cssClass: 'auth-modal-overlay',
      backdropDismiss: true,
      componentProps: {
        message: 'Create your account',
      }
    });
    await modal.present();
  }

  dismissBanner() {
    this.dismissed = true;
  }
}
