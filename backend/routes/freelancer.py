from flask import Blueprint, request, jsonify
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime
from dateutil.relativedelta import relativedelta

from app import mongo, serialize, serialize_list
from stats_helper import get_freelancer_stats

freelancer_bp = Blueprint('freelancer', __name__, url_prefix='/api/freelancer')

def freelancer_required(f):
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not current_user or current_user.get("role") != "freelancer":
            return jsonify({'error': 'Freelancer access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@freelancer_bp.route('/dashboard', methods=['GET'])
@freelancer_required
def get_dashboard(current_user):
    freelancer_id = str(current_user["_id"])
    stats = get_freelancer_stats(freelancer_id)
    
    # Active projects (max 5)
    active_projects = list(mongo.db.projects.find({"freelancer_id": freelancer_id, "status": "active"}).sort("created_at", -1).limit(5))
    for p in active_projects:
        client = mongo.db.users.find_one({"_id": ObjectId(p["client_id"])})
        if client:
            p["client"] = {
                "id": str(client["_id"]),
                "full_name": client.get("full_name"),
                "avatar_initials": client.get("full_name", "?")[0].upper() if client.get("full_name") else "?"
            }
            
    # Recent proposals (last 5)
    recent_proposals = list(mongo.db.proposals.find({"freelancer_id": freelancer_id}).sort("created_at", -1).limit(5))
    for prop in recent_proposals:
        offer = mongo.db.offers.find_one({"_id": ObjectId(prop["offer_id"])})
        if offer: prop["offer_title"] = offer.get("title")

    # Recent reviews (last 3 received)
    recent_reviews = list(mongo.db.projects.find({"freelancer_id": freelancer_id, "status": "completed", "freelancer_rating": {"$ne": None}}).sort("completed_at", -1).limit(3))
    reviews = []
    for p in recent_reviews:
        client = mongo.db.users.find_one({"_id": ObjectId(p["client_id"])})
        reviews.append({
            "project_title": p.get("title"),
            "rating": p.get("freelancer_rating"),
            "comment": p.get("freelancer_review_comment", ""),
            "date": p.get("completed_at"),
            "client": {
                "full_name": client.get("full_name") if client else "Unknown",
                "avatar_initials": client.get("full_name", "?")[0].upper() if client and client.get("full_name") else "?"
            }
        })

    return jsonify({
        "stats": stats,
        "active_projects": serialize_list(active_projects),
        "recent_proposals": serialize_list(recent_proposals),
        "recent_reviews": reviews
    }), 200

@freelancer_bp.route('/projects', methods=['GET'])
@freelancer_required
def get_projects(current_user):
    freelancer_id = str(current_user["_id"])
    status = request.args.get('status', 'all').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = {"freelancer_id": freelancer_id}
    if status != 'all':
        query["status"] = status
        
    total = mongo.db.projects.count_documents(query)
    projects = list(mongo.db.projects.find(query).sort("created_at", -1).skip((page - 1) * per_page).limit(per_page))
    
    for p in projects:
        client = mongo.db.users.find_one({"_id": ObjectId(p["client_id"])})
        if client:
            p["client"] = {
                "id": str(client["_id"]),
                "full_name": client.get("full_name"),
                "avatar_initials": client.get("full_name", "?")[0].upper() if client.get("full_name") else "?"
            }
        
        offer = mongo.db.offers.find_one({"_id": ObjectId(p["offer_id"])})
        if offer:
            p["offer"] = serialize(offer)
            
    return jsonify({
        "projects": serialize_list(projects),
        "total": total,
        "page": page,
        "per_page": per_page
    }), 200

@freelancer_bp.route('/earnings', methods=['GET'])
@freelancer_required
def get_earnings(current_user):
    freelancer_id = str(current_user["_id"])
    period = request.args.get('period', 'month')
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Total earnings
    pipeline_total = [{"$match": {"freelancer_id": freelancer_id, "status": "completed"}}, {"$group": {"_id": None, "total": {"$sum": "$budget"}}}]
    res_total = list(mongo.db.projects.aggregate(pipeline_total))
    total_earned = res_total[0]["total"] if res_total else 0

    # This period / Last period
    if period == 'month':
        start_this = datetime.datetime(now.year, now.month, 1, tzinfo=datetime.timezone.utc)
        start_last = start_this - relativedelta(months=1)
    else: # year
        start_this = datetime.datetime(now.year, 1, 1, tzinfo=datetime.timezone.utc)
        start_last = datetime.datetime(now.year - 1, 1, 1, tzinfo=datetime.timezone.utc)

    def sum_budget(query):
        res = list(mongo.db.projects.aggregate([{"$match": query}, {"$group": {"_id": None, "total": {"$sum": "$budget"}}}]))
        return res[0]["total"] if res else 0

    this_period = sum_budget({"freelancer_id": freelancer_id, "status": "completed", "completed_at": {"$gte": start_this}})
    last_period = sum_budget({"freelancer_id": freelancer_id, "status": "completed", "completed_at": {"$gte": start_last, "$lt": start_this}})

    # By month (last 6 months)
    by_month = []
    for i in range(5, -1, -1):
        m_start = datetime.datetime(now.year, now.month, 1, tzinfo=datetime.timezone.utc) - relativedelta(months=i)
        m_end = m_start + relativedelta(months=1)
        amount = sum_budget({"freelancer_id": freelancer_id, "status": "completed", "completed_at": {"$gte": m_start, "$lt": m_end}})
        by_month.append({"month": m_start.strftime("%b"), "amount": amount})

    # By project
    by_project = []
    projects = list(mongo.db.projects.find({"freelancer_id": freelancer_id, "status": "completed"}).sort("completed_at", -1))
    for p in projects:
        by_project.append({
            "title": p.get("title"),
            "amount": p.get("budget"),
            "date": p.get("completed_at")
        })

    return jsonify({
        "total": total_earned,
        "this_period": this_period,
        "last_period": last_period,
        "by_month": by_month,
        "by_project": by_project
    }), 200

@freelancer_bp.route('/reviews', methods=['GET'])
@freelancer_required
def get_reviews(current_user):
    freelancer_id = str(current_user["_id"])
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = {"freelancer_id": freelancer_id, "status": "completed", "freelancer_rating": {"$ne": None}}
    total = mongo.db.projects.count_documents(query)
    
    reviews_cursor = mongo.db.projects.find(query).sort("completed_at", -1).skip((page - 1) * per_page).limit(per_page)
    reviews = []
    for p in reviews_cursor:
        client = mongo.db.users.find_one({"_id": ObjectId(p["client_id"])})
        reviews.append({
            "id": str(p["_id"]),
            "project_title": p.get("title"),
            "rating": p.get("freelancer_rating"),
            "comment": p.get("freelancer_review_comment", ""),
            "date": p.get("completed_at"),
            "client": {
                "full_name": client.get("full_name") if client else "Unknown",
                "avatar_initials": client.get("full_name", "?")[0].upper() if client and client.get("full_name") else "?"
            }
        })
        
    return jsonify({
        "reviews": reviews,
        "total": total,
        "page": page,
        "per_page": per_page
    }), 200
