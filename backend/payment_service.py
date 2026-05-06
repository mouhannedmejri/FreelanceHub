"""
Stripe Payment Service
======================
Handles all Stripe-related operations:
- Payment intents
- Subscription billing
- Refunds
- Webhook processing
"""

import os
import stripe
import datetime
from bson import ObjectId

# Initialize Stripe – falls back gracefully if key not set
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')


def is_stripe_configured():
    """Check if Stripe API key is configured."""
    return bool(stripe.api_key and stripe.api_key.startswith('sk_'))


def create_payment_intent(amount, currency='eur', metadata=None):
    """
    Create a Stripe PaymentIntent.
    amount: float in major currency units (e.g. 19.99)
    """
    if not is_stripe_configured():
        # Return mock intent for development
        return {
            'id': f'pi_mock_{ObjectId()}',
            'client_secret': f'pi_mock_{ObjectId()}_secret_mock',
            'amount': int(amount * 100),
            'currency': currency,
            'status': 'requires_payment_method',
            'metadata': metadata or {},
            '_mock': True
        }

    intent = stripe.PaymentIntent.create(
        amount=int(amount * 100),
        currency=currency,
        metadata=metadata or {},
        automatic_payment_methods={'enabled': True},
    )
    return {
        'id': intent.id,
        'client_secret': intent.client_secret,
        'amount': intent.amount,
        'currency': intent.currency,
        'status': intent.status,
        'metadata': dict(intent.metadata),
        '_mock': False
    }


def confirm_payment_intent(payment_intent_id):
    """Retrieve and verify status of a PaymentIntent."""
    if not is_stripe_configured() or payment_intent_id.startswith('pi_mock_'):
        return {'status': 'succeeded', '_mock': True}
    intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    return {'status': intent.status, '_mock': False}


def create_refund(payment_intent_id, amount=None):
    """Create a refund for a payment."""
    if not is_stripe_configured() or payment_intent_id.startswith('pi_mock_'):
        return {'id': f'rf_mock_{ObjectId()}', 'status': 'succeeded', '_mock': True}

    params = {'payment_intent': payment_intent_id}
    if amount:
        params['amount'] = int(amount * 100)
    refund = stripe.Refund.create(**params)
    return {'id': refund.id, 'status': refund.status, '_mock': False}


def create_subscription_checkout(customer_email, price_id, success_url, cancel_url, metadata=None):
    """Create a Stripe Checkout Session for subscriptions."""
    if not is_stripe_configured():
        return {
            'id': f'cs_mock_{ObjectId()}',
            'url': success_url + '?session_id=mock_session',
            '_mock': True
        }

    session = stripe.checkout.Session.create(
        mode='subscription',
        customer_email=customer_email,
        line_items=[{'price': price_id, 'quantity': 1}],
        success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=cancel_url,
        metadata=metadata or {},
    )
    return {'id': session.id, 'url': session.url, '_mock': False}


def cancel_subscription(stripe_subscription_id):
    """Cancel a Stripe subscription."""
    if not is_stripe_configured() or stripe_subscription_id.startswith('sub_mock_'):
        return {'status': 'canceled', '_mock': True}
    sub = stripe.Subscription.modify(stripe_subscription_id, cancel_at_period_end=True)
    return {'status': sub.status, 'cancel_at_period_end': sub.cancel_at_period_end, '_mock': False}


def construct_webhook_event(payload, sig_header):
    """Verify and construct a Stripe webhook event."""
    if not STRIPE_WEBHOOK_SECRET:
        return None
    return stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
