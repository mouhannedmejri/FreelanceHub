import { Injectable } from '@angular/core';
import { ModalController } from '@ionic/angular';
import { Router } from '@angular/router';
import { AuthModalComponent } from '../components/auth-modal/auth-modal.component';
import { GuestSessionService, IntendedAction } from './guest-session.service';

@Injectable({ providedIn: 'root' })
export class GuestAccessService {
  constructor(
    private modalCtrl: ModalController,
    private guestSession: GuestSessionService,
    private router: Router
  ) {}

  /**
   * Show the auth modal overlay when a guest tries a protected action.
   * Optionally store an intended action for post-login redirect.
   */
  async showAuthModal(
    message = 'Sign in to unlock this feature',
    intendedAction?: Partial<IntendedAction>
  ): Promise<boolean> {
    // Store intended action if provided
    if (intendedAction) {
      this.guestSession.setIntendedAction({
        type: intendedAction.type || 'action',
        targetId: intendedAction.targetId,
        route: intendedAction.route,
        data: intendedAction.data,
        timestamp: Date.now()
      });
    }

    const modal = await this.modalCtrl.create({
      component: AuthModalComponent,
      cssClass: 'auth-modal-overlay',
      backdropDismiss: true,
      componentProps: {
        message,
        intendedRoute: intendedAction?.route
      }
    });

    await modal.present();
    const { data } = await modal.onDidDismiss();
    return !!data?.authenticated;
  }

  /**
   * Legacy method for backward compatibility.
   * Now shows the full auth modal instead of a simple alert.
   */
  async showSignupPrompt(message = 'Sign up to unlock this feature.'): Promise<void> {
    await this.showAuthModal(message);
  }
}
