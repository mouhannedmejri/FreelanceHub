import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ToastController, LoadingController } from '@ionic/angular';

@Component({
  selector: 'app-auth',
  templateUrl: './auth.page.html',
  styleUrls: ['./auth.page.scss'],
  standalone: false,
})
export class AuthPage {
  activeTab: 'login' | 'register' = 'login';

  // Login fields
  loginEmail = '';
  loginPassword = '';

  // Register fields
  registerFullName = '';
  registerEmail = '';
  registerPassword = '';
  registerRole: 'freelancer' | 'client' = 'freelancer';
  acceptTerms = false;

  constructor(
    private authService: AuthService,
    private router: Router,
    private toastCtrl: ToastController,
    private loadingCtrl: LoadingController
  ) {}

  switchTab(tab: 'login' | 'register') {
    this.activeTab = tab;
  }

  async onLogin() {
    if (!this.loginEmail || !this.loginPassword) {
      this.showToast('Veuillez remplir tous les champs', 'warning');
      return;
    }

    const loading = await this.loadingCtrl.create({
      message: 'Connexion...',
      spinner: 'crescent',
    });
    await loading.present();

    this.authService
      .login({ email: this.loginEmail, password: this.loginPassword })
      .subscribe({
        next: (res) => {
          loading.dismiss();
          this.showToast(`Bienvenue, ${res.user.full_name}!`, 'success');
          this.router.navigate(['/home'], { replaceUrl: true });
        },
        error: (err) => {
          loading.dismiss();
          const msg = err.error?.error || 'Erreur de connexion';
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
      this.showToast('Veuillez remplir tous les champs', 'warning');
      return;
    }
    if (!this.acceptTerms) {
      this.showToast('Veuillez accepter les conditions', 'warning');
      return;
    }

    const loading = await this.loadingCtrl.create({
      message: 'Création du compte...',
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
          this.showToast('Compte créé avec succès!', 'success');
          if (res.user.role === 'freelancer') {
            this.router.navigate(['/onboarding'], { replaceUrl: true });
          } else {
            this.router.navigate(['/home'], { replaceUrl: true });
          }
        },
        error: (err) => {
          loading.dismiss();
          const msg = err.error?.error || "Erreur lors de l'inscription";
          this.showToast(msg, 'danger');
        },
      });
  }

  async demoLogin(role: 'freelancer' | 'client' | 'admin') {
    const credentials: Record<string, { email: string; password: string }> = {
      freelancer: { email: 'freelancer@demo.com', password: 'password123' },
      client: { email: 'client@demo.com', password: 'password123' },
      admin: { email: 'admin@demo.com', password: 'password123' },
    };

    const cred = credentials[role];
    const loading = await this.loadingCtrl.create({
      message: `Connexion ${role}...`,
      spinner: 'crescent',
    });
    await loading.present();

    this.authService.login(cred).subscribe({
      next: (res) => {
        loading.dismiss();
        this.showToast(`Bienvenue, ${res.user.full_name}!`, 'success');
        this.router.navigate(['/home'], { replaceUrl: true });
      },
      error: (err) => {
        loading.dismiss();
        const msg = err.error?.error || 'Erreur de connexion demo';
        this.showToast(msg, 'danger');
      },
    });
  }

  selectRole(role: 'freelancer' | 'client') {
    this.registerRole = role;
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
