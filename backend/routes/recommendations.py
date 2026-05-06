from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime

from app import mongo, serialize, serialize_list
from recommendation_engine import (
    score_offer_for_client,
    score_freelancer_for_client,
    score_offer_for_freelancer,
)

recommendations_bp = Blueprint("recommendations", __name__, url_prefix="/api/recommendations")


def _safe_object_id(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


def _not_interested_ids(user_id: str, item_type: str):
    docs = mongo.db.recommendation_feedback.find({"user_id": user_id, "item_type": item_type, "action": "not_interested"})
    return {d.get("item_id") for d in docs}


@recommendations_bp.route("/offers", methods=["GET"])
@jwt_required()
def get_offer_recommendations():
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user or user.get("role") != "client":
        return jsonify({"error": "Client access required"}), 403

    limit = min(request.args.get("limit", 10, type=int), 30)
    skip = max(request.args.get("skip", 0, type=int), 0)

    interests = user.get("interests", [])
    client_projects = list(mongo.db.projects.find({"client_id": user_id, "status": {"$in": ["completed", "active"]}}, {"budget": 1}))
    budget_values = [float(p.get("budget") or 0) for p in client_projects if float(p.get("budget") or 0) > 0]
    avg_budget = sum(budget_values) / len(budget_values) if budget_values else 0

    hidden_ids = _not_interested_ids(user_id, "offer")
    offers = list(
        mongo.db.offers.find(
            {"status": "active", "_id": {"$nin": [ObjectId(i) for i in hidden_ids if _safe_object_id(i)]}},
            {"title": 1, "description": 1, "category": 1, "skills": 1, "budget_min": 1, "budget_max": 1, "proposals_count": 1, "created_at": 1, "client_id": 1},
        ).sort("created_at", -1).limit(120)
    )

    scored = []
    for offer in offers:
        enrich = score_offer_for_client(offer, interests, avg_budget)
        offer["recommendation"] = enrich
        scored.append(offer)

    scored.sort(key=lambda x: x["recommendation"]["score"], reverse=True)
    total = len(scored)
    paged = scored[skip : skip + limit]
    for item in paged:
        client = mongo.db.users.find_one({"_id": ObjectId(item["client_id"])}, {"full_name": 1})
        item["client_name"] = client.get("full_name") if client else "Client"

    return jsonify({"data": serialize_list(paged), "meta": {"total": total, "limit": limit, "skip": skip, "has_more": (skip + limit) < total}}), 200


@recommendations_bp.route("/freelancers", methods=["GET"])
@jwt_required()
def get_freelancer_recommendations():
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user or user.get("role") != "client":
        return jsonify({"error": "Client access required"}), 403

    limit = min(request.args.get("limit", 10, type=int), 30)
    skip = max(request.args.get("skip", 0, type=int), 0)
    interests = user.get("interests", [])
    hidden_ids = _not_interested_ids(user_id, "freelancer")

    pipeline = [
        {"$match": {"role": "freelancer", "status": {"$ne": "banned"}}},
        {"$lookup": {"from": "freelancer_profiles", "let": {"uid": {"$toString": "$_id"}}, "pipeline": [{"$match": {"$expr": {"$eq": ["$user_id", "$$uid"]}}}], "as": "profile"}},
        {"$unwind": {"path": "$profile", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {"from": "reviews", "let": {"uid": {"$toString": "$_id"}}, "pipeline": [{"$match": {"$expr": {"$eq": ["$target_id", "$$uid"]}}}, {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}, "total_reviews": {"$sum": 1}}}], "as": "review_data"}},
        {"$addFields": {"review_data": {"$ifNull": [{"$arrayElemAt": ["$review_data", 0]}, {}]}, "avg_rating": {"$ifNull": [{"$arrayElemAt": ["$review_data.avg_rating", 0]}, {"$ifNull": ["$profile.avg_rating", 0]}]}, "total_reviews": {"$ifNull": [{"$arrayElemAt": ["$review_data.total_reviews", 0]}, {"$ifNull": ["$profile.total_reviews", 0]}]}}},
        {"$project": {"full_name": 1, "last_login_at": 1, "is_online": {"$gte": ["$last_login_at", {"$dateSubtract": {"startDate": "$$NOW", "unit": "minute", "amount": 5}}]}, "avg_rating": 1, "total_reviews": 1, "profile": {"title": "$profile.title", "skills": {"$ifNull": ["$profile.skills", []]}, "hourly_rate": {"$ifNull": ["$profile.hourly_rate", 0]}, "location": {"$ifNull": ["$profile.location", "Remote"]}, "portfolio": {"$ifNull": ["$profile.portfolio", []]}}}},
    ]
    freelancers = [f for f in list(mongo.db.users.aggregate(pipeline)) if str(f.get("_id")) not in hidden_ids]

    scored = []
    for f in freelancers:
        f["recommendation"] = score_freelancer_for_client(f, interests)
        scored.append(f)
    scored.sort(key=lambda x: x["recommendation"]["score"], reverse=True)
    total = len(scored)
    paged = scored[skip : skip + limit]
    return jsonify({"data": serialize_list(paged), "meta": {"total": total, "limit": limit, "skip": skip, "has_more": (skip + limit) < total}}), 200


@recommendations_bp.route("/opportunities", methods=["GET"])
@jwt_required()
def get_opportunity_recommendations():
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user or user.get("role") != "freelancer":
        return jsonify({"error": "Freelancer access required"}), 403

    limit = min(request.args.get("limit", 10, type=int), 30)
    skip = max(request.args.get("skip", 0, type=int), 0)

    profile = mongo.db.freelancer_profiles.find_one({"user_id": user_id}) or {}
    skills = profile.get("skills", [])
    hidden_ids = _not_interested_ids(user_id, "opportunity")
    offers = list(
        mongo.db.offers.find(
            {"status": "active", "_id": {"$nin": [ObjectId(i) for i in hidden_ids if _safe_object_id(i)]}},
            {"title": 1, "description": 1, "category": 1, "skills": 1, "budget_min": 1, "budget_max": 1, "proposals_count": 1, "created_at": 1, "client_id": 1},
        ).sort("created_at", -1).limit(120)
    )
    scored = []
    for offer in offers:
        offer["recommendation"] = score_offer_for_freelancer(offer, skills)
        scored.append(offer)
    scored.sort(key=lambda x: x["recommendation"]["score"], reverse=True)
    total = len(scored)
    paged = scored[skip : skip + limit]
    for item in paged:
        client = mongo.db.users.find_one({"_id": ObjectId(item["client_id"])}, {"full_name": 1})
        item["client_name"] = client.get("full_name") if client else "Client"
    return jsonify({"data": serialize_list(paged), "meta": {"total": total, "limit": limit, "skip": skip, "has_more": (skip + limit) < total}}), 200


@recommendations_bp.route("/track", methods=["POST"])
@jwt_required()
def track_recommendation_interaction():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    item_id = str(data.get("item_id", "")).strip()
    item_type = str(data.get("item_type", "")).strip()
    action = str(data.get("action", "")).strip()
    recommendation_type = str(data.get("recommendation_type", "")).strip()
    if not item_id or not item_type or not action:
        return jsonify({"error": "item_id, item_type and action are required"}), 400

    mongo.db.recommendation_interactions.insert_one(
        {
            "user_id": user_id,
            "item_id": item_id,
            "item_type": item_type,
            "recommendation_type": recommendation_type,
            "action": action,
            "score": data.get("score"),
            "reason": data.get("reason", ""),
            "metadata": data.get("metadata", {}),
            "created_at": datetime.datetime.now(datetime.timezone.utc),
        }
    )
    return jsonify({"ok": True}), 200


@recommendations_bp.route("/not-interested", methods=["POST"])
@jwt_required()
def mark_not_interested():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    item_id = str(data.get("item_id", "")).strip()
    item_type = str(data.get("item_type", "")).strip()
    if not item_id or not item_type:
        return jsonify({"error": "item_id and item_type are required"}), 400

    mongo.db.recommendation_feedback.update_one(
        {"user_id": user_id, "item_id": item_id, "item_type": item_type},
        {"$set": {"action": "not_interested", "updated_at": datetime.datetime.now(datetime.timezone.utc)}},
        upsert=True,
    )
    return jsonify({"ok": True}), 200
