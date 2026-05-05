import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { GuestSessionService } from '../../services/guest-session.service';
import { ToastController, LoadingController } from '@ionic/angular';

@Component({
  selector: 'app-auth',
  templateUrl: './auth.page.html',
  styleUrls: ['./auth.page.scss'],
  standalone: false,
})
export class AuthPage implements OnInit {
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
    private authService: AuthService,
    private guestSession: GuestSessionService,
    private route: ActivatedRoute,
    private router: Router,
    private toastCtrl: ToastController,
    private loadingCtrl: LoadingController
  ) {}

  ngOnInit() {
    const tab = this.route.snapshot.queryParamMap.get('tab');
    if (tab === 'register' || tab === 'login') {
      this.activeTab = tab;
    }

    // Pre-select role if coming from role-selection page
    const role = this.route.snapshot.queryParamMap.get('role');
    if (role === 'client' || role === 'freelancer') {
      this.registerRole = role;
    }

    this.authService.currentUser$.subscribe(user => {
      if (user) {
        this.router.navigate(['/home'], { replaceUrl: true });
      }
    });
  }

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
          const redirectRoute = this.guestSession.getPostLoginRoute();
          this.guestSession.clearIntendedAction();
          this.router.navigate([redirectRoute], { replaceUrl: true });
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
    if (this.registerPassword !== this.registerConfirmPassword) {
      this.showToast('Les mots de passe ne correspondent pas', 'warning');
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
          this.router.navigate(['/onboarding'], { replaceUrl: true });
        },
        error: (err) => {
          loading.dismiss();
          const msg = err.error?.error || "Erreur lors de l'inscription";
          this.showToast(msg, 'danger');
        },
      });
  }

  browseAsGuest() {
    this.authService.enterGuestMode();
    this.router.navigate(['/home'], { replaceUrl: true });
  }

  onForgotPassword() {
    this.showToast('Fonctionnalité bientôt disponible', 'warning');
  }

  onSocialLogin(provider: 'google' | 'facebook') {
    this.showToast(`${provider.toUpperCase()} OAuth bientôt disponible`, 'warning');
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
