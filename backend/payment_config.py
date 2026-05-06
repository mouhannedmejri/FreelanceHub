"""
FreelanceHub Monetization Configuration
========================================
Central configuration for all revenue streams:
- Commission rates per transaction type
- Subscription tier definitions
- Boost/featured listing pricing
- Premium à la carte features
- Service fees
"""

import datetime

# ─── 1. COMMISSION RATES ────────────────────────────────────────────

COMMISSION_RATES = {
    'project_commission': {
        'freelancer_fee': 0.15,   # 15% from freelancer earnings
        'client_fee': 0.03,       # 3% processing fee from client
    },
    'store_commission': {
        'seller_fee': 0.20,       # 20% from digital product sales
    },
    'service_commission': {
        'provider_fee': 0.12,     # 12% from service sales
    }
}


def calculate_commission(amount, transaction_type, user_role='freelancer', subscription_plan='free'):
    """
    Calculate platform commission based on transaction type, user role,
    and subscription tier (subscribers get reduced rates).
    """
    commission = 0.0
    net_amount = amount
    total_amount = amount

    # Subscription-based rate override
    plan_features = SUBSCRIPTION_PLANS.get(subscription_plan, SUBSCRIPTION_PLANS['free'])
    plan_commission_rate = plan_features['features'].get('commission_rate')

    if transaction_type == 'project':
        if user_role == 'freelancer':
            rate = plan_commission_rate or COMMISSION_RATES['project_commission']['freelancer_fee']
            commission = round(amount * rate, 2)
            net_amount = round(amount - commission, 2)
        else:  # client
            rate = COMMISSION_RATES['project_commission']['client_fee']
            commission = round(amount * rate, 2)
            total_amount = round(amount + commission, 2)
            net_amount = amount

    elif transaction_type == 'store':
        rate = COMMISSION_RATES['store_commission']['seller_fee']
        # Pro/Business sellers get a small discount
        if subscription_plan == 'pro':
            rate = 0.17
        elif subscription_plan == 'business':
            rate = 0.15
        commission = round(amount * rate, 2)
        net_amount = round(amount - commission, 2)

    elif transaction_type == 'service':
        rate = plan_commission_rate or COMMISSION_RATES['service_commission']['provider_fee']
        commission = round(amount * rate, 2)
        net_amount = round(amount - commission, 2)

    return {
        'gross_amount': amount,
        'commission': commission,
        'commission_rate': rate if 'rate' in dir() else 0,
        'net_amount': net_amount,
        'total_charged': total_amount,
        'transaction_type': transaction_type,
        'subscription_plan': subscription_plan
    }


# ─── 2. SUBSCRIPTION PLANS ─────────────────────────────────────────

SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'billing_period': None,
        'stripe_price_id': None,
        'features': {
            'proposals_per_month': 10,
            'offers_per_month': 3,
            'commission_rate': 0.15,
            'store_listings': 2,
            'featured_listing': False,
            'priority_support': False,
            'analytics': 'basic',
            'verified_badge': False,
            'dedicated_manager': False,
            'api_access': False
        }
    },
    'pro': {
        'name': 'Professional',
        'price': 19.99,
        'billing_period': 'monthly',
        'stripe_price_id': 'price_pro_monthly',  # Replace with actual Stripe price ID
        'features': {
            'proposals_per_month': 50,
            'offers_per_month': 15,
            'commission_rate': 0.12,
            'store_listings': 10,
            'featured_listing': True,
            'priority_support': True,
            'analytics': 'advanced',
            'verified_badge': True,
            'dedicated_manager': False,
            'api_access': False
        }
    },
    'business': {
        'name': 'Business',
        'price': 49.99,
        'billing_period': 'monthly',
        'stripe_price_id': 'price_business_monthly',  # Replace with actual Stripe price ID
        'features': {
            'proposals_per_month': 'unlimited',
            'offers_per_month': 'unlimited',
            'commission_rate': 0.10,
            'store_listings': 'unlimited',
            'featured_listing': True,
            'priority_support': True,
            'analytics': 'premium',
            'verified_badge': True,
            'dedicated_manager': True,
            'api_access': True
        }
    }
}


def get_user_plan_features(plan_name):
    """Get the feature set for a given plan."""
    plan = SUBSCRIPTION_PLANS.get(plan_name, SUBSCRIPTION_PLANS['free'])
    return plan['features']


def check_plan_limit(plan_name, feature, current_usage):
    """Check if user has exceeded a plan limit. Returns (allowed, limit)."""
    features = get_user_plan_features(plan_name)
    limit = features.get(feature)
    if limit == 'unlimited':
        return True, 'unlimited'
    if isinstance(limit, int):
        return current_usage < limit, limit
    return True, None


# ─── 3. BOOST / FEATURED LISTING PRICING ───────────────────────────

BOOST_PRICING = {
    'offer_featured_7days': {
        'price': 9.99,
        'duration_days': 7,
        'target': 'offer',
        'label': 'Boost Offer – 7 days'
    },
    'offer_featured_30days': {
        'price': 29.99,
        'duration_days': 30,
        'target': 'offer',
        'label': 'Boost Offer – 30 days'
    },
    'service_featured_7days': {
        'price': 7.99,
        'duration_days': 7,
        'target': 'service',
        'label': 'Feature Service – 7 days'
    },
    'store_product_featured_7days': {
        'price': 14.99,
        'duration_days': 7,
        'target': 'store_product',
        'label': 'Feature Product – 7 days'
    },
    'profile_boost_7days': {
        'price': 12.99,
        'duration_days': 7,
        'target': 'profile',
        'label': 'Profile Boost – 7 days'
    }
}


# ─── 4. PREMIUM À LA CARTE FEATURES ────────────────────────────────

PREMIUM_FEATURES = {
    'urgent_badge': {
        'price': 4.99,
        'duration_days': 3,
        'description': 'Add URGENT badge to your offer',
        'icon': 'alert-circle-outline'
    },
    'portfolio_video': {
        'price': 14.99,
        'duration_days': 365,
        'description': 'Upload video to portfolio',
        'icon': 'videocam-outline'
    },
    'advanced_analytics': {
        'price': 9.99,
        'duration_days': 30,
        'description': 'Detailed profile visitor analytics',
        'icon': 'analytics-outline'
    },
    'proposal_template': {
        'price': 2.99,
        'duration_days': 365,
        'description': 'Save unlimited proposal templates',
        'icon': 'document-text-outline'
    }
}


# ─── 5. SERVICE FEES ───────────────────────────────────────────────

SERVICE_FEES = {
    'payment_processing': 0.029,      # 2.9%
    'payment_processing_fixed': 0.30, # + $0.30 per transaction
    'withdrawal_fee': 1.00,           # $1 per withdrawal
    'rush_payout': 4.99,              # Instant payout (vs 5-7 days)
    'currency_conversion': 0.03       # 3% for international payments
}


# ─── 6. ADVERTISING PLACEMENTS ─────────────────────────────────────

AD_PLACEMENTS = {
    'homepage_banner': {
        'price_monthly': 500,
        'dimensions': '728x90',
        'label': 'Homepage Banner'
    },
    'search_results_sponsored': {
        'price_monthly': 300,
        'dimensions': '300x250',
        'label': 'Sponsored Search Result'
    },
    'email_newsletter': {
        'price_monthly': 200,
        'dimensions': '600x200',
        'label': 'Newsletter Sponsor'
    }
}
