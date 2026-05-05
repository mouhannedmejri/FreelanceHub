import { Component, Input, OnInit } from '@angular/core';
import { ModalController, ToastController, LoadingController } from '@ionic/angular';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { GuestSessionService } from '../../services/guest-session.service';

@Component({
  selector: 'app-auth-modal',
  templateUrl: './auth-modal.component.html',
  styleUrls: ['./auth-modal.component.scss'],
  standalone: false,
})
export class AuthModalComponent implements OnInit {
  @Input() message = 'Sign in to continue';
  @Input() intendedRoute?: string;

  activeTab: 'login' | 'register' = 'login';

  // Login fields
  loginEmail = '';
  loginPassword = '';

  // Register fields
  registerFullName = '';
  registerEmail = '';
  registerPassword = '';
  registerConfirmPassword = '';
  registerRole: 'freelancer' | 'client' = 'freelancer';

  constructor(
    private modalCtrl: ModalController,
    private toastCtrl: ToastController,
    private loadingCtrl: LoadingController,
    private authService: AuthService,
    private guestSession: GuestSessionService,
    private router: Router
  ) {}

  ngOnInit() {}

  switchTab(tab: 'login' | 'register') {
    this.activeTab = tab;
  }

  dismiss() {
    this.modalCtrl.dismiss({ authenticated: false });
  }

  async onLogin() {
    if (!this.loginEmail || !this.loginPassword) {
      this.showToast('Please fill in all fields', 'warning');
      return;
    }

    const loading = await this.loadingCtrl.create({
      message: 'Signing in...',
      spinner: 'crescent',
    });
    await loading.present();

    this.authService
      .login({ email: this.loginEmail, password: this.loginPassword })
      .subscribe({
        next: (res) => {
          loading.dismiss();
          this.showToast(`Welcome, ${res.user.full_name}!`, 'success');
          this.handleAuthSuccess();
        },
        error: (err) => {
          loading.dismiss();
          const msg = err.error?.error || 'Login failed';
          this.showToast(msg, 'danger');
        },
      });
  }

  async onRegister() {
    if (
      !this.registerFullName ||
      !this.registerEmail ||
      !this.registerPassword
    ) {
      this.showToast('Please fill in all fields', 'warning');
      return;
    }
    if (this.registerPassword !== this.registerConfirmPassword) {
      this.showToast('Passwords do not match', 'warning');
      return;
    }

    const loading = await this.loadingCtrl.create({
      message: 'Creating account...',
      spinner: 'crescent',
    });
    await loading.present();

    this.authService
      .register({
        full_name: this.registerFullName,
        email: this.registerEmail,
        password: this.registerPassword,
        role: this.registerRole,
      })
      .subscribe({
        next: (res) => {
          loading.dismiss();
          this.showToast('Account created!', 'success');
          this.handleAuthSuccess();
        },
        error: (err) => {
          loading.dismiss();
          const msg = err.error?.error || 'Registration failed';
          this.showToast(msg, 'danger');
        },
      });
  }

  selectRole(role: 'freelancer' | 'client') {
    this.registerRole = role;
  }

  private handleAuthSuccess() {
    // Consume the intended action and decide redirect
    const action = this.guestSession.consumeIntendedAction();
    const redirectRoute = action?.route || this.intendedRoute || '/home';

    this.modalCtrl.dismiss({ authenticated: true, redirectRoute });

    // Navigate to the intended route
    if (redirectRoute && redirectRoute !== '/home') {
      setTimeout(() => {
        this.router.navigate([redirectRoute], { replaceUrl: false });
      }, 300);
    }
  }

  private async showToast(
    message: string,
    color: 'success' | 'danger' | 'warning'
  ) {
    const toast = await this.toastCtrl.create({
      message,
      duration: 3000,
      color,
      position: 'top',
    });
    await toast.present();
  }
}
