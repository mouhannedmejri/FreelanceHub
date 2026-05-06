"""
Subscription Management Routes
===============================
Handles subscription creation, cancellation, plan changes, and status checks.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime

from app import mongo, serialize, serialize_list
from payment_config import SUBSCRIPTION_PLANS, get_user_plan_features
from payment_service import (
    create_subscription_checkout, cancel_subscription,
    confirm_payment_intent, is_stripe_configured
)

subscriptions_bp = Blueprint('subscriptions', __name__, url_prefix='/api/subscriptions')


# ─── GET PLANS ──────────────────────────────────────────────────────

@subscriptions_bp.route('/plans', methods=['GET'])
def get_plans():
    """Get all available subscription plans."""
    plans = []
    for key, plan in SUBSCRIPTION_PLANS.items():
        plans.append({
            'id': key,
            'name': plan['name'],
            'price': plan['price'],
            'billing_period': plan.get('billing_period'),
            'features': plan['features']
        })
    return jsonify({'plans': plans}), 200


# ─── CURRENT SUBSCRIPTION ──────────────────────────────────────────

@subscriptions_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_subscription():
    """Get user's current subscription details."""
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    plan_name = user.get("subscription_plan", "free") if user else "free"

    # Find active subscription record
    sub = mongo.db.subscriptions.find_one({
        "user_id": user_id,
        "status": {"$in": ["active", "trialing"]}
    })

    plan_info = SUBSCRIPTION_PLANS.get(plan_name, SUBSCRIPTION_PLANS['free'])

    return jsonify({
        'plan': plan_name,
        'plan_info': {
            'name': plan_info['name'],
            'price': plan_info['price'],
            'features': plan_info['features']
        },
        'subscription': serialize(sub) if sub else None,
        'is_active': plan_name != 'free'
    }), 200


# ─── SUBSCRIBE ──────────────────────────────────────────────────────

@subscriptions_bp.route('/subscribe', methods=['POST'])
@jwt_required()
def subscribe():
    """Subscribe to a plan."""
    user_id = get_jwt_identity()
    data = request.get_json()
    plan = data.get('plan', '')

    if plan not in ['pro', 'business']:
        return jsonify({'error': 'Invalid plan. Choose pro or business.'}), 400

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    current_plan = user.get("subscription_plan", "free")
    if current_plan == plan:
        return jsonify({'error': 'Already subscribed to this plan'}), 400

    plan_info = SUBSCRIPTION_PLANS[plan]
    now = datetime.datetime.now(datetime.timezone.utc)

    # If Stripe is configured, create a Checkout Session
    if is_stripe_configured() and plan_info.get('stripe_price_id'):
        checkout = create_subscription_checkout(
            customer_email=user.get('email', ''),
            price_id=plan_info['stripe_price_id'],
            success_url=data.get('success_url', 'http://localhost:8100/pricing?status=success'),
            cancel_url=data.get('cancel_url', 'http://localhost:8100/pricing?status=cancelled'),
            metadata={'user_id': user_id, 'plan': plan}
        )
        return jsonify({
            'checkout_url': checkout['url'],
            'session_id': checkout['id'],
            'is_mock': checkout.get('_mock', False)
        }), 200

    # Mock/development mode: activate immediately
    # Cancel any existing subscription
    mongo.db.subscriptions.update_many(
        {"user_id": user_id, "status": "active"},
        {"$set": {"status": "cancelled", "cancelled_at": now}}
    )

    sub_doc = {
        "user_id": user_id,
        "plan": plan,
        "price": plan_info['price'],
        "billing_period": plan_info.get('billing_period', 'monthly'),
        "status": "active",
        "stripe_subscription_id": None,
        "started_at": now,
        "current_period_start": now,
        "current_period_end": now + datetime.timedelta(days=30),
        "next_billing_date": now + datetime.timedelta(days=30),
        "auto_renew": True,
        "created_at": now
    }
    mongo.db.subscriptions.insert_one(sub_doc)

    # Update user
    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "subscription_plan": plan,
            "subscription_updated_at": now
        }}
    )

    # Create notification
    mongo.db.notifications.insert_one({
        "user_id": user_id,
        "type": "subscription",
        "title": f"Bienvenue dans {plan_info['name']} ! 🎉",
        "body": f"Votre abonnement {plan_info['name']} est maintenant actif.",
        "is_read": False,
        "created_at": now
    })

    return jsonify({
        'message': f'Subscribed to {plan_info["name"]}',
        'plan': plan,
        'features': plan_info['features'],
        'is_mock': True
    }), 200


# ─── CANCEL SUBSCRIPTION ───────────────────────────────────────────

@subscriptions_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel_sub():
    """Cancel current subscription (at end of billing period)."""
    user_id = get_jwt_identity()
    now = datetime.datetime.now(datetime.timezone.utc)

    sub = mongo.db.subscriptions.find_one({
        "user_id": user_id, "status": "active"
    })
    if not sub:
        return jsonify({'error': 'No active subscription'}), 400

    # Cancel with Stripe if applicable
    if sub.get("stripe_subscription_id"):
        cancel_subscription(sub["stripe_subscription_id"])

    # Mark as cancelling (stays active until period end)
    mongo.db.subscriptions.update_one(
        {"_id": sub["_id"]},
        {"$set": {
            "auto_renew": False,
            "cancel_requested_at": now,
            "status": "cancelling"
        }}
    )

    return jsonify({
        'message': 'Subscription will be cancelled at end of billing period',
        'active_until': sub.get("current_period_end", now).isoformat()
    }), 200


# ─── CHANGE PLAN ────────────────────────────────────────────────────

@subscriptions_bp.route('/change-plan', methods=['POST'])
@jwt_required()
def change_plan():
    """Upgrade or downgrade subscription plan."""
    user_id = get_jwt_identity()
    data = request.get_json()
    new_plan = data.get('plan', '')

    if new_plan not in SUBSCRIPTION_PLANS:
        return jsonify({'error': 'Invalid plan'}), 400

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    current_plan = user.get("subscription_plan", "free") if user else "free"

    if new_plan == current_plan:
        return jsonify({'error': 'Already on this plan'}), 400

    now = datetime.datetime.now(datetime.timezone.utc)

    if new_plan == 'free':
        # Downgrade to free = cancel
        mongo.db.subscriptions.update_many(
            {"user_id": user_id, "status": {"$in": ["active", "cancelling"]}},
            {"$set": {"status": "cancelled", "cancelled_at": now}}
        )
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"subscription_plan": "free", "subscription_updated_at": now}}
        )
        return jsonify({'message': 'Downgraded to Free plan', 'plan': 'free'}), 200

    # For paid plans, go through subscribe flow
    return subscribe()


# ─── CHECK FEATURE ACCESS ──────────────────────────────────────────

@subscriptions_bp.route('/check-feature', methods=['POST'])
@jwt_required()
def check_feature():
    """Check if user has access to a feature based on their subscription."""
    user_id = get_jwt_identity()
    data = request.get_json()
    feature = data.get('feature', '')

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    plan_name = user.get("subscription_plan", "free") if user else "free"
    features = get_user_plan_features(plan_name)

    has_access = features.get(feature, False)
    if has_access == 'unlimited':
        has_access = True

    return jsonify({
        'feature': feature,
        'has_access': bool(has_access),
        'plan': plan_name,
        'value': features.get(feature)
    }), 200


# ─── WEBHOOK (Stripe) ──────────────────────────────────────────────

@subscriptions_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events for subscription changes."""
    from payment_service import construct_webhook_event

    payload = request.data
    sig_header = request.headers.get('Stripe-Signature', '')

    try:
        event = construct_webhook_event(payload, sig_header)
    except Exception:
        return jsonify({'error': 'Invalid signature'}), 400

    if not event:
        return jsonify({'status': 'webhook not configured'}), 200

    now = datetime.datetime.now(datetime.timezone.utc)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('metadata', {}).get('user_id')
        plan = session.get('metadata', {}).get('plan')
        if user_id and plan:
            mongo.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"subscription_plan": plan, "subscription_updated_at": now}}
            )

    elif event['type'] == 'customer.subscription.deleted':
        sub = event['data']['object']
        stripe_sub_id = sub['id']
        mongo.db.subscriptions.update_one(
            {"stripe_subscription_id": stripe_sub_id},
            {"$set": {"status": "cancelled", "cancelled_at": now}}
        )
        # Find user and reset plan
        db_sub = mongo.db.subscriptions.find_one({"stripe_subscription_id": stripe_sub_id})
        if db_sub:
            mongo.db.users.update_one(
                {"_id": ObjectId(db_sub["user_id"])},
                {"$set": {"subscription_plan": "free"}}
            )

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        stripe_sub_id = invoice.get('subscription')
        if stripe_sub_id:
            mongo.db.subscriptions.update_one(
                {"stripe_subscription_id": stripe_sub_id},
                {"$set": {"status": "past_due"}}
            )

    return jsonify({'status': 'ok'}), 200
