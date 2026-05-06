import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface CommissionBreakdown {
  gross_amount: number;
  commission: number;
  commission_rate: number;
  net_amount: number;
  total_charged: number;
  transaction_type: string;
  subscription_plan: string;
}

export interface PaymentIntentResponse {
  client_secret: string;
  payment_intent_id: string;
  breakdown: CommissionBreakdown;
  is_mock: boolean;
}

export interface WalletInfo {
  balance: number;
  total_earned: number;
  total_commission_paid: number;
  total_withdrawn: number;
  transaction_count: number;
}

export interface BoostOption {
  id: string;
  price: number;
  duration_days: number;
  target: string;
  label: string;
}

export interface PremiumFeature {
  id: string;
  price: number;
  duration_days: number;
  description: string;
  icon: string;
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  billing_period: string | null;
  features: {
    proposals_per_month: number | string;
    offers_per_month: number | string;
    commission_rate: number;
    store_listings: number | string;
    featured_listing: boolean;
    priority_support: boolean;
    analytics: string;
    verified_badge: boolean;
    dedicated_manager: boolean;
    api_access: boolean;
  };
}

export interface SubscriptionInfo {
  plan: string;
  plan_info: SubscriptionPlan;
  subscription: any;
  is_active: boolean;
}

@Injectable({ providedIn: 'root' })
export class PaymentService {
  private paymentsUrl = `${environment.apiUrl}/payments`;
  private subsUrl = `${environment.apiUrl}/subscriptions`;

  constructor(private http: HttpClient) {}

  // ─── Payment Intents ──────────────────────────────────────

  createPaymentIntent(amount: number, type: string, relatedId?: string): Observable<PaymentIntentResponse> {
    return this.http.post<PaymentIntentResponse>(`${this.paymentsUrl}/create-intent`, {
      amount, type, related_id: relatedId || ''
    });
  }

  confirmPayment(paymentIntentId: string, type: string, sellerId: string, amount: number, relatedId: string): Observable<any> {
    return this.http.post(`${this.paymentsUrl}/confirm`, {
      payment_intent_id: paymentIntentId,
      type, seller_id: sellerId, amount, related_id: relatedId
    });
  }

  // ─── Fee Calculator ───────────────────────────────────────

  calculateFees(amount: number, type: string, plan?: string): Observable<{ freelancer: CommissionBreakdown; client: CommissionBreakdown }> {
    return this.http.post<any>(`${this.paymentsUrl}/calculate`, { amount, type, plan: plan || 'free' });
  }

  // ─── Transaction History ──────────────────────────────────

  getTransactions(type?: string, page?: number): Observable<any> {
    const params: any = {};
    if (type) params.type = type;
    if (page) params.page = page;
    return this.http.get(`${this.paymentsUrl}/transactions`, { params });
  }

  // ─── Wallet ───────────────────────────────────────────────

  getWallet(): Observable<WalletInfo> {
    return this.http.get<WalletInfo>(`${this.paymentsUrl}/wallet`);
  }

  requestWithdrawal(amount: number, method: string, rush?: boolean): Observable<any> {
    return this.http.post(`${this.paymentsUrl}/withdraw`, { amount, method, rush: rush || false });
  }

  // ─── Boost ────────────────────────────────────────────────

  getBoostOptions(): Observable<{ options: BoostOption[] }> {
    return this.http.get<{ options: BoostOption[] }>(`${this.paymentsUrl}/boost/options`);
  }

  purchaseBoost(boostType: string, targetId: string, paymentIntentId: string): Observable<any> {
    return this.http.post(`${this.paymentsUrl}/boost`, {
      boost_type: boostType, target_id: targetId, payment_intent_id: paymentIntentId
    });
  }

  // ─── Premium Features ────────────────────────────────────

  getPremiumFeatures(): Observable<{ features: PremiumFeature[] }> {
    return this.http.get<{ features: PremiumFeature[] }>(`${this.paymentsUrl}/premium/features`);
  }

  purchasePremiumFeature(featureId: string, paymentIntentId: string): Observable<any> {
    return this.http.post(`${this.paymentsUrl}/premium/purchase`, {
      feature_id: featureId, payment_intent_id: paymentIntentId
    });
  }

  getActivePremiumFeatures(): Observable<any> {
    return this.http.get(`${this.paymentsUrl}/premium/active`);
  }

  // ─── Subscriptions ────────────────────────────────────────

  getPlans(): Observable<{ plans: SubscriptionPlan[] }> {
    return this.http.get<{ plans: SubscriptionPlan[] }>(`${this.subsUrl}/plans`);
  }

  getCurrentSubscription(): Observable<SubscriptionInfo> {
    return this.http.get<SubscriptionInfo>(`${this.subsUrl}/current`);
  }

  subscribe(plan: string): Observable<any> {
    return this.http.post(`${this.subsUrl}/subscribe`, { plan });
  }

  cancelSubscription(): Observable<any> {
    return this.http.post(`${this.subsUrl}/cancel`, {});
  }

  changePlan(plan: string): Observable<any> {
    return this.http.post(`${this.subsUrl}/change-plan`, { plan });
  }

  checkFeatureAccess(feature: string): Observable<{ feature: string; has_access: boolean; plan: string; value: any }> {
    return this.http.post<any>(`${this.subsUrl}/check-feature`, { feature });
  }
}
