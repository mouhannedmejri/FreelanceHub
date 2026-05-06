import { Component, OnInit } from '@angular/core';
import { PaymentService, SubscriptionPlan, PremiumFeature, BoostOption } from '../../services/payment.service';
import { AuthService } from '../../services/auth.service';
import { GuestAccessService } from '../../services/guest-access.service';
import { ToastController, AlertController } from '@ionic/angular';
import { Router } from '@angular/router';

type PlanFeatureKey = keyof SubscriptionPlan['features'];
type PlanFeatureValue = SubscriptionPlan['features'][PlanFeatureKey];

@Component({
  selector: 'app-pricing',
  templateUrl: './pricing.page.html',
  styleUrls: ['./pricing.page.scss'],
  standalone: false
})
export class PricingPage implements OnInit {
  plans: SubscriptionPlan[] = [];
  premiumFeatures: PremiumFeature[] = [];
  boostOptions: BoostOption[] = [];
  currentPlan = 'free';
  isLoading = true;
  isSubscribing = false;
  billingToggle: 'monthly' | 'yearly' = 'monthly';
  activeSection = 'plans'; // plans, features, boosts
  comparisonFeatureKeys: PlanFeatureKey[] = [
    'proposals_per_month',
    'offers_per_month',
    'commission_rate',
    'store_listings',
    'featured_listing',
    'priority_support',
    'analytics',
    'verified_badge',
    'dedicated_manager',
    'api_access'
  ];

  constructor(
    private paymentService: PaymentService,
    private authService: AuthService,
    private guestAccessService: GuestAccessService,
    private toastController: ToastController,
    private alertController: AlertController,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadData();
  }

  get isGuest(): boolean {
    return this.authService.isGuest;
  }

  loadData() {
    this.isLoading = true;

    this.paymentService.getPlans().subscribe({
      next: (res) => {
        this.plans = res.plans || [];
        this.isLoading = false;
      },
      error: () => { this.isLoading = false; }
    });

    if (!this.isGuest) {
      this.paymentService.getCurrentSubscription().subscribe({
        next: (res) => { this.currentPlan = res.plan || 'free'; }
      });
    }

    this.paymentService.getPremiumFeatures().subscribe({
      next: (res) => { this.premiumFeatures = res.features || []; }
    });

    this.paymentService.getBoostOptions().subscribe({
      next: (res) => { this.boostOptions = res.options || []; }
    });
  }

  getPlanById(id: string): SubscriptionPlan | undefined {
    return this.plans.find(p => p.id === id);
  }

  isCurrentPlan(planId: string): boolean {
    return this.currentPlan === planId;
  }

  isUpgrade(planId: string): boolean {
    const order = ['free', 'pro', 'business'];
    return order.indexOf(planId) > order.indexOf(this.currentPlan);
  }

  getPlanButtonText(planId: string): string {
    if (this.isCurrentPlan(planId)) return 'Plan actuel';
    if (this.isUpgrade(planId)) return 'Upgrade';
    return 'Changer de plan';
  }

  getFeatureDisplay(value: PlanFeatureValue): string {
    if (value === true) return '✓';
    if (value === false) return '✗';
    if (value === 'unlimited') return '∞';
    return String(value);
  }

  getFeatureLabel(key: PlanFeatureKey): string {
    const labels: Record<PlanFeatureKey, string> = {
      proposals_per_month: 'Propositions/mois',
      offers_per_month: 'Offres/mois',
      commission_rate: 'Commission',
      store_listings: 'Produits en boutique',
      featured_listing: 'Mise en avant',
      priority_support: 'Support prioritaire',
      analytics: 'Analytics',
      verified_badge: 'Badge vérifié',
      dedicated_manager: 'Manager dédié',
      api_access: 'Accès API'
    };
    return labels[key];
  }

  getFeatureLabelFromString(key: string): string {
    return this.getFeatureLabel(key as PlanFeatureKey);
  }

  getCommissionDisplay(rate: PlanFeatureValue): string {
    if (typeof rate === 'number') {
      return `${(rate * 100).toFixed(0)}%`;
    }
    return String(rate);
  }

  getPlanFeature(plan: SubscriptionPlan, key: PlanFeatureKey): PlanFeatureValue {
    return plan.features[key];
  }

  getSavingsDisplay(planId: string): string {
    if (planId === 'pro') return 'Économisez 3% de commission';
    if (planId === 'business') return 'Économisez 5% de commission';
    return '';
  }

  async subscribe(planId: string) {
    if (this.isGuest) {
      this.guestAccessService.showSignupPrompt('Inscrivez-vous pour accéder aux plans premium.');
      return;
    }

    if (this.isCurrentPlan(planId) || planId === 'free') return;

    const plan = this.getPlanById(planId);
    if (!plan) return;

    const alert = await this.alertController.create({
      header: 'Confirmer l\'abonnement',
      message: `Passer au plan ${plan.name} pour ${plan.price}€/mois ?`,
      cssClass: 'dark-alert',
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        {
          text: 'Confirmer',
          handler: () => this.processSubscription(planId)
        }
      ]
    });
    await alert.present();
  }

  processSubscription(planId: string) {
    this.isSubscribing = true;
    this.paymentService.subscribe(planId).subscribe({
      next: async (res) => {
        this.isSubscribing = false;
        this.currentPlan = planId;

        if (res.checkout_url && !res.is_mock) {
          window.open(res.checkout_url, '_blank');
          return;
        }

        const toast = await this.toastController.create({
          message: `🎉 Bienvenue dans le plan ${res.plan || planId} !`,
          duration: 4000, color: 'success'
        });
        toast.present();
      },
      error: async (err) => {
        this.isSubscribing = false;
        const toast = await this.toastController.create({
          message: err.error?.error || 'Erreur lors de l\'abonnement.',
          duration: 3000, color: 'danger'
        });
        toast.present();
      }
    });
  }

  async cancelSubscription() {
    const alert = await this.alertController.create({
      header: 'Annuler l\'abonnement',
      message: 'Votre abonnement sera actif jusqu\'à la fin de la période de facturation.',
      cssClass: 'dark-alert',
      buttons: [
        { text: 'Garder', role: 'cancel' },
        {
          text: 'Annuler le plan',
          role: 'destructive',
          handler: () => {
            this.paymentService.cancelSubscription().subscribe({
              next: async () => {
                this.currentPlan = 'free';
                const toast = await this.toastController.create({
                  message: 'Abonnement annulé.', duration: 3000, color: 'warning'
                });
                toast.present();
              }
            });
          }
        }
      ]
    });
    await alert.present();
  }

  async purchaseFeature(feature: PremiumFeature) {
    if (this.isGuest) {
      this.guestAccessService.showSignupPrompt('Inscrivez-vous pour accéder aux fonctionnalités premium.');
      return;
    }

    const alert = await this.alertController.create({
      header: feature.description,
      message: `Acheter pour ${feature.price}€ ?`,
      cssClass: 'dark-alert',
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        {
          text: 'Acheter',
          handler: () => {
            this.paymentService.createPaymentIntent(feature.price, 'premium_feature', feature.id).subscribe({
              next: (intent) => {
                this.paymentService.purchasePremiumFeature(feature.id, intent.payment_intent_id).subscribe({
                  next: async () => {
                    const toast = await this.toastController.create({
                      message: `✅ ${feature.description} activé !`, duration: 3000, color: 'success'
                    });
                    toast.present();
                  }
                });
              }
            });
          }
        }
      ]
    });
    await alert.present();
  }

  goBack() {
    this.router.navigate(['/home']);
  }
}
