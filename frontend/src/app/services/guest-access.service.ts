import { Injectable } from '@angular/core';
import { AlertController } from '@ionic/angular';
import { Router } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class GuestAccessService {
  constructor(private alertController: AlertController, private router: Router) {}

  async showSignupPrompt(message = 'Sign up to apply and unlock this feature.'): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Create an account',
      message,
      buttons: [
        {
          text: 'Continue exploring',
          role: 'cancel',
        },
        {
          text: 'Sign up',
          handler: () => this.router.navigate(['/auth'], { queryParams: { tab: 'register' } }),
        },
      ],
    });
    await alert.present();
  }
}
