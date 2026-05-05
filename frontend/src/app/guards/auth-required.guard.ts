import { Injectable } from '@angular/core';
import { CanActivate, Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { ModalController } from '@ionic/angular';
import { AuthService } from '../services/auth.service';
import { GuestSessionService, IntendedAction } from '../services/guest-session.service';
import { AuthModalComponent } from '../components/auth-modal/auth-modal.component';

/**
 * AuthRequiredGuard – triggers an authentication modal when a guest
 * tries to navigate to a protected route.
 *
 * If the user is authenticated, passes through normally.
 * If the user is a guest / unauthenticated, the guard:
 *   1. Saves the intended route as an IntendedAction.
 *   2. Opens the AuthModalComponent as an overlay.
 *   3. If auth succeeds in the modal, navigates to the intended route.
 *   4. If the user dismisses the modal, blocks navigation.
 */
@Injectable({ providedIn: 'root' })
export class AuthRequiredGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private guestSession: GuestSessionService,
    private modalCtrl: ModalController,
    private router: Router
  ) {}

  async canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Promise<boolean> {
    if (this.authService.isAuthenticated) {
      return true;
    }

    // Store intended route
    const intendedAction: IntendedAction = {
      type: 'navigate',
      route: state.url,
      timestamp: Date.now()
    };
    this.guestSession.setIntendedAction(intendedAction);

    // Show auth modal
    const modal = await this.modalCtrl.create({
      component: AuthModalComponent,
      cssClass: 'auth-modal-overlay',
      backdropDismiss: true,
      componentProps: {
        message: 'Sign in to access this feature',
        intendedRoute: state.url
      }
    });

    await modal.present();

    const { data } = await modal.onDidDismiss();
    if (data?.authenticated) {
      // Auth succeeded — allow navigation
      return true;
    }

    // User dismissed — stay where they are
    return false;
  }
}
