from flask import Blueprint, request, jsonify
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from app import mongo, serialize, serialize_list

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def admin_required(f):
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not current_user or current_user.get("role") != "admin":
            return jsonify({'error': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

from stats_helper import get_admin_stats
import datetime

@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats(current_user):
    """Admin dashboard statistics."""
    stats = get_admin_stats()
    return jsonify(stats), 200

@admin_bp.route('/approvals/counts', methods=['GET'])
@admin_required
def get_approval_counts(current_user):
    pending = mongo.db.approval_requests.count_documents({"status": "pending"})
    approved = mongo.db.approval_requests.count_documents({"status": "approved"})
    rejected = mongo.db.approval_requests.count_documents({"status": "rejected"})
    return jsonify({"pending": pending, "approved": approved, "rejected": rejected}), 200

@admin_bp.route('/approvals', methods=['GET'])
@admin_required
def get_approvals(current_user):
    req_type = request.args.get('type', '').strip()
    status = request.args.get('status', 'pending').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = {}
    if req_type:
        query["type"] = req_type
    if status != 'all':
        query["status"] = status
        
    total = mongo.db.approval_requests.count_documents(query)
    approvals = list(mongo.db.approval_requests.find(query)
                     .sort("created_at", -1)
                     .skip((page - 1) * per_page)
                     .limit(per_page))
                     
    for app in approvals:
        requester = mongo.db.users.find_one({"_id": ObjectId(app["requester_id"])})
        if requester:
            app["requester"] = {
                "id": str(requester["_id"]),
                "full_name": requester.get("full_name"),
                "email": requester.get("email")
            }
        
        ref_id = app.get("reference_id")
        if ref_id:
            if app["type"] == "offer":
                ref_doc = mongo.db.offers.find_one({"_id": ObjectId(ref_id)})
            else:
                ref_doc = mongo.db.services.find_one({"_id": ObjectId(ref_id)})
            app["reference"] = serialize(ref_doc) if ref_doc else None

    return jsonify({
        "approvals": serialize_list(approvals),
        "total": total,
        "page": page,
        "per_page": per_page
    }), 200

@admin_bp.route('/approvals/<app_id>', methods=['PATCH'])
@admin_required
def update_approval(current_user, app_id):
    data = request.get_json()
    status = data.get("status")
    admin_note = data.get("admin_note", "").strip()
    
    if status not in ["approved", "rejected"]:
        return jsonify({"error": "Invalid status"}), 400
        
    if status == "rejected" and not admin_note:
        return jsonify({"error": "Admin note required for rejection"}), 400
        
    app_req = mongo.db.approval_requests.find_one({"_id": ObjectId(app_id)})
    if not app_req:
        return jsonify({"error": "Approval request not found"}), 404
        
    now = datetime.datetime.now(datetime.timezone.utc)
    mongo.db.approval_requests.update_one(
        {"_id": ObjectId(app_id)},
        {"$set": {"status": status, "admin_note": admin_note, "reviewed_at": now}}
    )
    
    ref_id = app_req.get("reference_id")
    if ref_id:
        coll = mongo.db.offers if app_req["type"] == "offer" else mongo.db.services
        coll.update_one({"_id": ObjectId(ref_id)}, {"$set": {"approval_status": status}})
        
    notif = {
        "user_id": app_req["requester_id"],
        "type": "approval",
        "title": "Demande d'approbation mise à jour",
        "body": f"Votre demande pour {'l\'offre' if app_req['type'] == 'offer' else 'le service'} a été {status}.",
        "is_read": False,
        "created_at": now
    }
    mongo.db.notifications.insert_one(notif)
    
    app_req["status"] = status
    app_req["admin_note"] = admin_note
    return jsonify({"approval": serialize(app_req)}), 200

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users(current_user):
    role = request.args.get('role', '').strip()
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    
    query = {}
    if role and role != 'all':
        if role == 'pending_approval':
            query["is_approved"] = False
            query["role"] = "freelancer"
        else:
            query["role"] = role
            
    if status and status != 'all':
        query["status"] = status
        
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
        
    total = mongo.db.users.count_documents(query)
    users = list(mongo.db.users.find(query)
                 .sort("created_at", -1)
                 .skip((page - 1) * per_page)
                 .limit(per_page))
                 
    for u in users:
        stats = {}
        if u.get("role") == "freelancer":
            stats["projects_count"] = mongo.db.projects.count_documents({"freelancer_id": str(u["_id"])})
            prof = mongo.db.freelancer_profiles.find_one({"user_id": str(u["_id"])})
            stats["rating"] = prof.get("avg_rating", 0) if prof else 0
        elif u.get("role") == "client":
            stats["projects_count"] = mongo.db.projects.count_documents({"client_id": str(u["_id"])})
        u["stats"] = stats
        
    return jsonify({
        'users': serialize_list(users),
        'total': total,
        'page': page,
        'per_page': per_page
    }), 200

@admin_bp.route('/users/<user_id>/ban', methods=['PATCH'])
@admin_required
def ban_user(current_user, user_id):
    data = request.get_json()
    reason = data.get("reason", "").strip()
    expires_at = data.get("expires_at")
    
    if len(reason) < 20:
        return jsonify({"error": "Reason must be at least 20 characters"}), 400
        
    now = datetime.datetime.now(datetime.timezone.utc)
    exp_date = datetime.datetime.fromisoformat(expires_at.replace('Z', '+00:00')) if expires_at else None
    
    mongo.db.user_bans.insert_one({
        "user_id": user_id,
        "reason": reason,
        "banned_by": str(current_user["_id"]),
        "banned_at": now,
        "expires_at": exp_date,
        "is_active": True
    })
    
    mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": "banned", "ban_reason": reason}})
    return jsonify({"message": "User banned successfully"}), 200

@admin_bp.route('/users/<user_id>/unban', methods=['PATCH'])
@admin_required
def unban_user(current_user, user_id):
    mongo.db.user_bans.update_many({"user_id": user_id, "is_active": True}, {"$set": {"is_active": False}})
    mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": "active", "ban_reason": None}})
    return jsonify({"message": "User unbanned successfully"}), 200

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(current_user, user_id):
    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)}, 
        {"$set": {"status": "deleted", "email": f"deleted_{user_id}@freelancehub.local"}}
    )
    
    now = datetime.datetime.now(datetime.timezone.utc)
    mongo.db.projects.update_many(
        {"$or": [{"client_id": user_id}, {"freelancer_id": user_id}], "status": "active"},
        {"$set": {"status": "cancelled", "completed_at": now}}
    )
    
    mongo.db.claims.update_many(
        {"$or": [{"claimant_id": user_id}, {"target_id": user_id}], "status": {"$in": ["open", "in_review"]}},
        {"$set": {"status": "resolved", "admin_note": "User deleted, claim auto-resolved", "resolved_at": now}}
    )
    
    return jsonify({"message": "User deleted successfully"}), 200

@admin_bp.route('/users/<user_id>/details', methods=['GET'])
@admin_required
def get_user_details(current_user, user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    projects = list(mongo.db.projects.find({"$or": [{"client_id": user_id}, {"freelancer_id": user_id}]}))
    claims = list(mongo.db.claims.find({"$or": [{"claimant_id": user_id}, {"target_id": user_id}]}))
    bans = list(mongo.db.user_bans.find({"user_id": user_id}).sort("banned_at", -1))
    
    return jsonify({
        "user": serialize(user),
        "projects": serialize_list(projects),
        "claims": serialize_list(claims),
        "bans": serialize_list(bans)
    }), 200

@admin_bp.route('/users/<user_id>/approve', methods=['PATCH'])
@admin_required
def toggle_approve(current_user, user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    new_status = not user.get("is_approved", False)
    mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_approved": new_status}})
    user["is_approved"] = new_status
    
    if new_status:
        now = datetime.datetime.now(datetime.timezone.utc)
        mongo.db.notifications.insert_one({
            "user_id": str(user["_id"]),
            "type": "system",
            "title": "Compte approuvé",
            "body": "Votre compte freelancer a été approuvé par un administrateur.",
            "is_read": False,
            "created_at": now
        })
    
    return jsonify({'user': serialize(user)}), 200

@admin_bp.route('/claims', methods=['GET'])
@admin_required
def get_claims(current_user):
    status = request.args.get('status', '').strip()
    priority = request.args.get('priority', '').strip()
    type_filter = request.args.get('type', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = {}
    if status and status != 'all': query["status"] = status
    if priority and priority != 'all': query["priority"] = priority
    if type_filter and type_filter != 'all': query["type"] = type_filter
        
    total = mongo.db.claims.count_documents(query)
    claims = list(mongo.db.claims.find(query).sort("created_at", -1).skip((page - 1) * per_page).limit(per_page))
    
    for c in claims:
        claimant = mongo.db.users.find_one({"_id": ObjectId(c["claimant_id"])})
        target = mongo.db.users.find_one({"_id": ObjectId(c["target_id"])})
        c["claimant"] = serialize(claimant) if claimant else None
        c["target"] = serialize(target) if target else None
        
    return jsonify({
        "claims": serialize_list(claims),
        "total": total,
        "page": page,
        "per_page": per_page
    }), 200

@admin_bp.route('/claims/<claim_id>', methods=['GET'])
@admin_required
def get_claim(current_user, claim_id):
    claim = mongo.db.claims.find_one({"_id": ObjectId(claim_id)})
    if not claim: return jsonify({"error": "Claim not found"}), 404
    
    claimant = mongo.db.users.find_one({"_id": ObjectId(claim["claimant_id"])})
    target = mongo.db.users.find_one({"_id": ObjectId(claim["target_id"])})
    claim["claimant"] = serialize(claimant) if claimant else None
    claim["target"] = serialize(target) if target else None
    
    if claim.get("project_id"):
        project = mongo.db.projects.find_one({"_id": ObjectId(claim["project_id"])})
        claim["project"] = serialize(project) if project else None
        
    return jsonify({"claim": serialize(claim)}), 200

@admin_bp.route('/claims/<claim_id>', methods=['PATCH'])
@admin_required
def update_claim(current_user, claim_id):
    data = request.get_json()
    status = data.get("status")
    admin_note = data.get("admin_note")
    priority = data.get("priority")
    
    update_data = {}
    if status: update_data["status"] = status
    if admin_note is not None: update_data["admin_note"] = admin_note
    if priority: update_data["priority"] = priority
    
    update_data["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
    if status == "resolved":
        update_data["resolved_at"] = datetime.datetime.now(datetime.timezone.utc)
        
    mongo.db.claims.update_one({"_id": ObjectId(claim_id)}, {"$set": update_data})
    
    updated_claim = mongo.db.claims.find_one({"_id": ObjectId(claim_id)})
    return jsonify({"claim": serialize(updated_claim)}), 200


# ─── REVENUE ANALYTICS ─────────────────────────────────────────────

@admin_bp.route('/revenue/stats', methods=['GET'])
@admin_required
def revenue_stats(current_user):
    """Comprehensive revenue analytics for admin dashboard."""
    from payment_config import SUBSCRIPTION_PLANS

    now = datetime.datetime.now(datetime.timezone.utc)

    # Revenue by month (from transactions)
    monthly_pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": {
                "year": {"$year": "$created_at"},
                "month": {"$month": "$created_at"}
            },
            "total_gross": {"$sum": "$gross_amount"},
            "total_commission": {"$sum": "$platform_commission"},
            "total_net_to_sellers": {"$sum": "$net_to_seller"},
            "transaction_count": {"$sum": 1}
        }},
        {"$sort": {"_id.year": -1, "_id.month": -1}},
        {"$limit": 12}
    ]
    revenue_by_month = list(mongo.db.transactions.aggregate(monthly_pipeline))

    # Revenue by type
    type_pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": "$type",
            "total_commission": {"$sum": "$platform_commission"},
            "count": {"$sum": 1}
        }}
    ]
    revenue_by_type = list(mongo.db.transactions.aggregate(type_pipeline))

    # Subscription stats
    active_subs = mongo.db.subscriptions.count_documents({"status": "active"})
    pro_subs = mongo.db.subscriptions.count_documents({"status": "active", "plan": "pro"})
    business_subs = mongo.db.subscriptions.count_documents({"status": "active", "plan": "business"})

    # MRR (Monthly Recurring Revenue)
    mrr = (pro_subs * SUBSCRIPTION_PLANS['pro']['price']) + \
          (business_subs * SUBSCRIPTION_PLANS['business']['price'])

    # Total platform earnings
    total_pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": None,
            "total_commission": {"$sum": "$platform_commission"},
            "total_volume": {"$sum": "$gross_amount"},
            "count": {"$sum": 1}
        }}
    ]
    total_result = list(mongo.db.transactions.aggregate(total_pipeline))
    totals = total_result[0] if total_result else {"total_commission": 0, "total_volume": 0, "count": 0}

    # Today's stats
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_pipeline = [
        {"$match": {"status": "completed", "created_at": {"$gte": today_start}}},
        {"$group": {
            "_id": None,
            "commission": {"$sum": "$platform_commission"},
            "volume": {"$sum": "$gross_amount"},
            "count": {"$sum": 1}
        }}
    ]
    today_result = list(mongo.db.transactions.aggregate(today_pipeline))
    today = today_result[0] if today_result else {"commission": 0, "volume": 0, "count": 0}

    # Pending withdrawals
    pending_withdrawals = mongo.db.withdrawals.count_documents({"status": "pending"})
    pending_amount_pipeline = [
        {"$match": {"status": "pending"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    pending_amount_result = list(mongo.db.withdrawals.aggregate(pending_amount_pipeline))
    pending_withdrawal_amount = pending_amount_result[0]["total"] if pending_amount_result else 0

    return jsonify({
        "revenue_by_month": serialize_list(revenue_by_month),
        "revenue_by_type": serialize_list(revenue_by_type),
        "subscriptions": {
            "active": active_subs,
            "pro": pro_subs,
            "business": business_subs,
            "mrr": round(mrr, 2)
        },
        "totals": {
            "platform_commission": totals.get("total_commission", 0),
            "transaction_volume": totals.get("total_volume", 0),
            "transaction_count": totals.get("count", 0)
        },
        "today": {
            "commission": today.get("commission", 0),
            "volume": today.get("volume", 0),
            "count": today.get("count", 0)
        },
        "withdrawals": {
            "pending_count": pending_withdrawals,
            "pending_amount": pending_withdrawal_amount
        }
    }), 200


@admin_bp.route('/revenue/transactions', methods=['GET'])
@admin_required
def revenue_transactions(current_user):
    """Get all platform transactions with filtering."""
    tx_type = request.args.get('type', '').strip()
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = {}
    if tx_type:
        query["type"] = tx_type
    if status:
        query["status"] = status

    total = mongo.db.transactions.count_documents(query)
    transactions = list(
        mongo.db.transactions.find(query)
        .sort("created_at", -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )

    for tx in transactions:
        buyer = mongo.db.users.find_one({"_id": ObjectId(tx["buyer_id"])}) if tx.get("buyer_id") and tx["buyer_id"] != "platform" else None
        seller = mongo.db.users.find_one({"_id": ObjectId(tx["seller_id"])}) if tx.get("seller_id") and tx["seller_id"] != "platform" else None
        tx["buyer_name"] = buyer.get("full_name", "") if buyer else "Platform"
        tx["seller_name"] = seller.get("full_name", "") if seller else "Platform"

    return jsonify({
        "transactions": serialize_list(transactions),
        "total": total,
        "page": page,
        "per_page": per_page
    }), 200


@admin_bp.route('/revenue/withdrawals', methods=['GET'])
@admin_required
def get_withdrawals(current_user):
    """Get all withdrawal requests."""
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = {}
    if status:
        query["status"] = status

    total = mongo.db.withdrawals.count_documents(query)
    withdrawals = list(
        mongo.db.withdrawals.find(query)
        .sort("requested_at", -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )

    for w in withdrawals:
        user = mongo.db.users.find_one({"_id": ObjectId(w["user_id"])})
        w["user_name"] = user.get("full_name", "") if user else ""

    return jsonify({
        "withdrawals": serialize_list(withdrawals),
        "total": total,
        "page": page,
        "per_page": per_page
    }), 200


@admin_bp.route('/revenue/withdrawals/<withdrawal_id>', methods=['PATCH'])
@admin_required
def process_withdrawal(current_user, withdrawal_id):
    """Approve or reject a withdrawal."""
    data = request.get_json()
    status = data.get("status")  # completed, rejected

    if status not in ["completed", "rejected"]:
        return jsonify({"error": "Invalid status"}), 400

    now = datetime.datetime.now(datetime.timezone.utc)
    update = {"status": status, "processed_at": now, "processed_by": str(current_user["_id"])}
    if status == "rejected":
        update["rejection_reason"] = data.get("reason", "")

    mongo.db.withdrawals.update_one({"_id": ObjectId(withdrawal_id)}, {"$set": update})
    return jsonify({"message": f"Withdrawal {status}"}), 200
