from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from app import mongo, serialize, serialize_list

earnings_bp = Blueprint('earnings', __name__, url_prefix='/api/freelancer/earnings')

@earnings_bp.route('/', methods=['GET'])
@jwt_required()
def get_earnings_breakdown():
    """Return earnings breakdown for freelancer."""
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user or user.get("role") != 'freelancer':
        return jsonify({'error': 'Unauthorized'}), 403

    # Calculate earnings from completed projects
    pipeline = [
        {"$match": {"freelancer_id": user_id, "status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$budget"}}}
    ]
    earnings_res = list(mongo.db.projects.aggregate(pipeline))
    total_earnings = earnings_res[0]["total"] if earnings_res else 0

    # Calculate pending earnings
    pending_pipeline = [
        {"$match": {"freelancer_id": user_id, "status": {"$in": ["active", "in_progress"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$budget"}}}
    ]
    pending_res = list(mongo.db.projects.aggregate(pending_pipeline))
    pending_earnings = pending_res[0]["total"] if pending_res else 0

    # Total withdrawn
    withdrawals = list(mongo.db.withdrawals.find({"user_id": user_id, "status": "completed"}))
    total_withdrawn = sum([w.get("amount", 0) for w in withdrawals])

    available_balance = max(0, total_earnings - total_withdrawn)

    return jsonify({
        "data": {
            "total_earnings": total_earnings,
            "pending_earnings": pending_earnings,
            "available_balance": available_balance,
            "total_withdrawn": total_withdrawn
        }
    }), 200

@earnings_bp.route('/withdraw', methods=['POST'])
@jwt_required()
def request_withdrawal():
    """Request to withdraw available funds."""
    user_id = get_jwt_identity()
    data = request.get_json()
    amount = float(data.get("amount", 0))

    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    pipeline = [
        {"$match": {"freelancer_id": user_id, "status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$budget"}}}
    ]
    earnings_res = list(mongo.db.projects.aggregate(pipeline))
    total_earnings = earnings_res[0]["total"] if earnings_res else 0

    withdrawals = list(mongo.db.withdrawals.find({"user_id": user_id, "status": {"$in": ["completed", "pending"]}}))
    total_withdrawn_and_pending = sum([w.get("amount", 0) for w in withdrawals])

    available_balance = total_earnings - total_withdrawn_and_pending

    if amount > available_balance:
        return jsonify({'error': 'Insufficient available funds'}), 400

    import datetime
    withdrawal_doc = {
        "user_id": user_id,
        "amount": amount,
        "status": "pending",
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    result = mongo.db.withdrawals.insert_one(withdrawal_doc)
    withdrawal_doc["_id"] = result.inserted_id

    return jsonify({"data": serialize(withdrawal_doc)}), 201
