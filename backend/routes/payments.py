"""
Payment & Transaction Routes
=============================
Handles payment intents, transaction recording, commission calculations,
boost purchases, and premium feature purchases.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime

from app import mongo, serialize, serialize_list
from payment_config import (
    calculate_commission, BOOST_PRICING, PREMIUM_FEATURES,
    SERVICE_FEES, SUBSCRIPTION_PLANS, get_user_plan_features
)
from payment_service import create_payment_intent, create_refund, confirm_payment_intent

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')


# ─── HELPERS ────────────────────────────────────────────────────────

def get_user_subscription_plan(user_id):
    """Get the current subscription plan for a user."""
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    return user.get("subscription_plan", "free") if user else "free"


def record_transaction(tx_type, buyer_id, seller_id, gross_amount, related_id,
                       payment_intent_id='', status='pending', metadata=None):
    """Record a transaction in the transactions collection."""
    plan = get_user_subscription_plan(seller_id)
    breakdown = calculate_commission(gross_amount, tx_type, 'freelancer', plan)

    now = datetime.datetime.now(datetime.timezone.utc)
    doc = {
        "type": tx_type,
        "buyer_id": buyer_id,
        "seller_id": seller_id,
        "gross_amount": gross_amount,
        "platform_commission": breakdown['commission'],
        "commission_rate": breakdown.get('commission_rate', 0),
        "net_to_seller": breakdown['net_amount'],
        "payment_intent_id": payment_intent_id,
        "payment_method": "stripe",
        "status": status,
        "related_id": related_id,
        "metadata": metadata or {},
        "created_at": now,
        "completed_at": now if status == 'completed' else None
    }
    result = mongo.db.transactions.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


# ─── CREATE PAYMENT INTENT ─────────────────────────────────────────

@payments_bp.route('/create-intent', methods=['POST'])
@jwt_required()
def create_intent():
    """Create a payment intent with commission breakdown."""
    user_id = get_jwt_identity()
    data = request.get_json()

    amount = data.get('amount')
    tx_type = data.get('type', 'project')  # project, store, service
    related_id = data.get('related_id', '')

    if not amount or amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    plan = get_user_subscription_plan(user_id)
    breakdown = calculate_commission(amount, tx_type, 'client', plan)

    intent = create_payment_intent(
        breakdown['total_charged'],
        currency='eur',
        metadata={
            'user_id': user_id,
            'type': tx_type,
            'related_id': related_id,
            'platform_commission': str(breakdown['commission'])
        }
    )

    return jsonify({
        'client_secret': intent['client_secret'],
        'payment_intent_id': intent['id'],
        'breakdown': breakdown,
        'is_mock': intent.get('_mock', False)
    }), 200


# ─── CONFIRM PAYMENT ───────────────────────────────────────────────

@payments_bp.route('/confirm', methods=['POST'])
@jwt_required()
def confirm_payment():
    """Confirm a completed payment and record the transaction."""
    user_id = get_jwt_identity()
    data = request.get_json()

    payment_intent_id = data.get('payment_intent_id', '')
    tx_type = data.get('type', 'project')
    seller_id = data.get('seller_id', '')
    amount = data.get('amount', 0)
    related_id = data.get('related_id', '')

    # Verify payment status with Stripe
    result = confirm_payment_intent(payment_intent_id)
    if result['status'] != 'succeeded':
        return jsonify({'error': 'Payment not completed', 'status': result['status']}), 400

    # Record transaction
    tx = record_transaction(
        tx_type=tx_type,
        buyer_id=user_id,
        seller_id=seller_id,
        gross_amount=amount,
        related_id=related_id,
        payment_intent_id=payment_intent_id,
        status='completed'
    )

    # Send notification to seller
    now = datetime.datetime.now(datetime.timezone.utc)
    mongo.db.notifications.insert_one({
        "user_id": seller_id,
        "type": "payment_received",
        "title": "Paiement reçu",
        "body": f"Vous avez reçu {tx['net_to_seller']}€ (après commission).",
        "is_read": False,
        "created_at": now
    })

    return jsonify({
        'message': 'Payment confirmed',
        'transaction': serialize(tx)
    }), 200


# ─── TRANSACTION HISTORY ───────────────────────────────────────────

@payments_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """Get user's transaction history."""
    user_id = get_jwt_identity()
    tx_type = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    query = {"$or": [{"buyer_id": user_id}, {"seller_id": user_id}]}
    if tx_type:
        query["type"] = tx_type

    total = mongo.db.transactions.count_documents(query)
    transactions = list(
        mongo.db.transactions.find(query)
        .sort("created_at", -1)
        .skip((page - 1) * limit)
        .limit(limit)
    )

    return jsonify({
        "data": serialize_list(transactions),
        "meta": {"page": page, "total": total, "has_more": (page * limit) < total}
    }), 200


# ─── COMMISSION CALCULATOR (PUBLIC PREVIEW) ────────────────────────

@payments_bp.route('/calculate', methods=['POST'])
def calculate_fees():
    """Calculate fees for a given amount (public, for UI display)."""
    data = request.get_json()
    amount = data.get('amount', 0)
    tx_type = data.get('type', 'project')
    plan = data.get('plan', 'free')

    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    freelancer_breakdown = calculate_commission(amount, tx_type, 'freelancer', plan)
    client_breakdown = calculate_commission(amount, tx_type, 'client', plan)

    return jsonify({
        'freelancer': freelancer_breakdown,
        'client': client_breakdown
    }), 200


# ─── BOOST / FEATURED LISTINGS ─────────────────────────────────────

@payments_bp.route('/boost', methods=['POST'])
@jwt_required()
def boost_listing():
    """Purchase a boost/featured listing for an offer, product, or profile."""
    user_id = get_jwt_identity()
    data = request.get_json()

    boost_type = data.get('boost_type', '')  # e.g. 'offer_featured_7days'
    target_id = data.get('target_id', '')
    payment_intent_id = data.get('payment_intent_id', '')

    if boost_type not in BOOST_PRICING:
        return jsonify({'error': 'Invalid boost type'}), 400

    boost = BOOST_PRICING[boost_type]
    now = datetime.datetime.now(datetime.timezone.utc)
    expires = now + datetime.timedelta(days=boost['duration_days'])

    # Verify payment
    result = confirm_payment_intent(payment_intent_id)
    if result['status'] != 'succeeded':
        return jsonify({'error': 'Payment not completed'}), 400

    # Apply the boost
    target = boost['target']
    collection_map = {
        'offer': 'offers',
        'service': 'services',
        'store_product': 'store_products',
        'profile': 'freelancer_profiles'
    }
    collection = collection_map.get(target)
    if collection and target_id:
        if target == 'profile':
            mongo.db[collection].update_one(
                {"user_id": user_id},
                {"$set": {
                    "is_boosted": True,
                    "boosted_until": expires,
                    "boosted_at": now
                }}
            )
        else:
            mongo.db[collection].update_one(
                {"_id": ObjectId(target_id)},
                {"$set": {
                    "is_featured": True,
                    "featured_until": expires,
                    "featured_at": now
                }}
            )

    # Record boost purchase
    mongo.db.boost_purchases.insert_one({
        "user_id": user_id,
        "boost_type": boost_type,
        "target": target,
        "target_id": target_id,
        "price": boost['price'],
        "payment_intent_id": payment_intent_id,
        "started_at": now,
        "expires_at": expires,
        "status": "active"
    })

    # Record as platform transaction
    record_transaction(
        tx_type='boost',
        buyer_id=user_id,
        seller_id='platform',
        gross_amount=boost['price'],
        related_id=target_id,
        payment_intent_id=payment_intent_id,
        status='completed'
    )

    return jsonify({
        'message': f'{boost["label"]} activated!',
        'expires_at': expires.isoformat()
    }), 200


@payments_bp.route('/boost/options', methods=['GET'])
def get_boost_options():
    """Get all available boost options."""
    options = []
    for key, val in BOOST_PRICING.items():
        options.append({
            'id': key,
            'price': val['price'],
            'duration_days': val['duration_days'],
            'target': val['target'],
            'label': val['label']
        })
    return jsonify({'options': options}), 200


# ─── PREMIUM FEATURES (À LA CARTE) ─────────────────────────────────

@payments_bp.route('/premium/purchase', methods=['POST'])
@jwt_required()
def purchase_premium_feature():
    """Purchase a premium feature."""
    user_id = get_jwt_identity()
    data = request.get_json()

    feature_id = data.get('feature_id', '')
    payment_intent_id = data.get('payment_intent_id', '')

    if feature_id not in PREMIUM_FEATURES:
        return jsonify({'error': 'Invalid feature'}), 400

    feature = PREMIUM_FEATURES[feature_id]
    now = datetime.datetime.now(datetime.timezone.utc)
    expires = now + datetime.timedelta(days=feature['duration_days'])

    # Verify payment
    result = confirm_payment_intent(payment_intent_id)
    if result['status'] != 'succeeded':
        return jsonify({'error': 'Payment not completed'}), 400

    # Grant feature to user
    mongo.db.user_premium_features.insert_one({
        "user_id": user_id,
        "feature_id": feature_id,
        "price": feature['price'],
        "payment_intent_id": payment_intent_id,
        "activated_at": now,
        "expires_at": expires,
        "status": "active"
    })

    record_transaction(
        tx_type='premium_feature',
        buyer_id=user_id,
        seller_id='platform',
        gross_amount=feature['price'],
        related_id=feature_id,
        payment_intent_id=payment_intent_id,
        status='completed'
    )

    return jsonify({
        'message': f'{feature["description"]} activated!',
        'feature': feature_id,
        'expires_at': expires.isoformat()
    }), 200


@payments_bp.route('/premium/features', methods=['GET'])
def get_premium_features():
    """Get all available premium features."""
    features = []
    for key, val in PREMIUM_FEATURES.items():
        features.append({
            'id': key,
            'price': val['price'],
            'duration_days': val['duration_days'],
            'description': val['description'],
            'icon': val.get('icon', 'star-outline')
        })
    return jsonify({'features': features}), 200


@payments_bp.route('/premium/active', methods=['GET'])
@jwt_required()
def get_active_features():
    """Get user's currently active premium features."""
    user_id = get_jwt_identity()
    now = datetime.datetime.now(datetime.timezone.utc)

    active = list(mongo.db.user_premium_features.find({
        "user_id": user_id,
        "status": "active",
        "expires_at": {"$gt": now}
    }))

    return jsonify({"features": serialize_list(active)}), 200


# ─── WALLET / EARNINGS ─────────────────────────────────────────────

@payments_bp.route('/wallet', methods=['GET'])
@jwt_required()
def get_wallet():
    """Get user's wallet balance and pending earnings."""
    user_id = get_jwt_identity()

    # Sum completed transactions where user is the seller
    pipeline = [
        {"$match": {"seller_id": user_id, "status": "completed"}},
        {"$group": {
            "_id": None,
            "total_earned": {"$sum": "$net_to_seller"},
            "total_commission_paid": {"$sum": "$platform_commission"},
            "transaction_count": {"$sum": 1}
        }}
    ]
    result = list(mongo.db.transactions.aggregate(pipeline))
    earnings = result[0] if result else {"total_earned": 0, "total_commission_paid": 0, "transaction_count": 0}

    # Pending (not yet withdrawn)
    withdrawn = 0
    withdrawals = list(mongo.db.withdrawals.find({"user_id": user_id, "status": "completed"}))
    withdrawn = sum(w.get("amount", 0) for w in withdrawals)

    balance = round(earnings.get("total_earned", 0) - withdrawn, 2)

    return jsonify({
        "balance": balance,
        "total_earned": earnings.get("total_earned", 0),
        "total_commission_paid": earnings.get("total_commission_paid", 0),
        "total_withdrawn": withdrawn,
        "transaction_count": earnings.get("transaction_count", 0)
    }), 200


@payments_bp.route('/withdraw', methods=['POST'])
@jwt_required()
def request_withdrawal():
    """Request a withdrawal of earnings."""
    user_id = get_jwt_identity()
    data = request.get_json()
    amount = data.get('amount', 0)
    method = data.get('method', 'bank_transfer')  # bank_transfer, paypal
    is_rush = data.get('rush', False)

    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    # Check balance
    pipeline = [
        {"$match": {"seller_id": user_id, "status": "completed"}},
        {"$group": {"_id": None, "total_earned": {"$sum": "$net_to_seller"}}}
    ]
    result = list(mongo.db.transactions.aggregate(pipeline))
    total_earned = result[0]["total_earned"] if result else 0

    withdrawals = list(mongo.db.withdrawals.find({"user_id": user_id, "status": {"$in": ["completed", "pending"]}}))
    total_withdrawn = sum(w.get("amount", 0) for w in withdrawals)

    balance = total_earned - total_withdrawn
    fee = SERVICE_FEES['rush_payout'] if is_rush else SERVICE_FEES['withdrawal_fee']

    if amount + fee > balance:
        return jsonify({'error': 'Insufficient balance'}), 400

    now = datetime.datetime.now(datetime.timezone.utc)
    payout_date = now if is_rush else now + datetime.timedelta(days=5)

    withdrawal = {
        "user_id": user_id,
        "amount": amount,
        "fee": fee,
        "net_amount": round(amount - fee, 2),
        "method": method,
        "is_rush": is_rush,
        "status": "pending",
        "requested_at": now,
        "estimated_payout": payout_date
    }
    mongo.db.withdrawals.insert_one(withdrawal)

    return jsonify({
        "message": "Withdrawal requested",
        "net_amount": withdrawal['net_amount'],
        "estimated_payout": payout_date.isoformat()
    }), 200
