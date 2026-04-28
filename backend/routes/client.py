from flask import Blueprint, request, jsonify
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from app import mongo, serialize, serialize_list
from stats_helper import get_client_stats
import datetime

client_bp = Blueprint('client', __name__, url_prefix='/api/client')

def client_required(f):
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not current_user or current_user.get("role") != "client":
            return jsonify({'error': 'Client access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@client_bp.route('/dashboard', methods=['GET'])
@client_required
def get_dashboard(current_user):
    client_id = str(current_user["_id"])
    stats = get_client_stats(client_id)
    
    # Active projects (max 5)
    active_projects = list(mongo.db.projects.find({"client_id": client_id, "status": "active"}).sort("created_at", -1).limit(5))
    for p in active_projects:
        freelancer = mongo.db.users.find_one({"_id": ObjectId(p["freelancer_id"])})
        if freelancer:
            p["freelancer"] = {
                "id": str(freelancer["_id"]),
                "full_name": freelancer.get("full_name"),
                "avatar_initials": freelancer.get("full_name", "?")[0].upper() if freelancer.get("full_name") else "?"
            }
            prof = mongo.db.freelancer_profiles.find_one({"user_id": p["freelancer_id"]})
            if prof: p["freelancer"]["rating"] = prof.get("avg_rating", 0)
    
    # Recent offers (last 3)
    recent_offers = list(mongo.db.offers.find({"client_id": client_id}).sort("created_at", -1).limit(3))
    for o in recent_offers:
        o["proposals_count"] = mongo.db.proposals.count_documents({"offer_id": str(o["_id"])})
        
    # Pending proposals
    offer_ids = [str(o["_id"]) for o in mongo.db.offers.find({"client_id": client_id})]
    pending_proposals = list(mongo.db.proposals.find({"offer_id": {"$in": offer_ids}, "status": "pending"}).sort("created_at", -1))
    for prop in pending_proposals:
        freelancer = mongo.db.users.find_one({"_id": ObjectId(prop["freelancer_id"])})
        if freelancer:
            prop["freelancer"] = {
                "id": str(freelancer["_id"]),
                "full_name": freelancer.get("full_name"),
                "avatar_initials": freelancer.get("full_name", "?")[0].upper() if freelancer.get("full_name") else "?"
            }
            prof = mongo.db.freelancer_profiles.find_one({"user_id": prop["freelancer_id"]})
            if prof: prop["freelancer"]["rating"] = prof.get("avg_rating", 0)
        offer = mongo.db.offers.find_one({"_id": ObjectId(prop["offer_id"])})
        if offer: prop["offer_title"] = offer.get("title")

    # Recent activity
    activity = []
    for prop in pending_proposals[:5]:
        activity.append({"desc": f"{prop['freelancer'].get('full_name')} a postulé à {prop.get('offer_title')}", "date": prop["created_at"], "type": "proposal"})
    for p in mongo.db.projects.find({"client_id": client_id, "status": "completed"}).sort("completed_at", -1).limit(5):
        activity.append({"desc": f"Projet {p.get('title')} terminé", "date": p.get("completed_at"), "type": "project"})
    
    activity.sort(key=lambda x: x["date"] if x["date"] else "", reverse=True)
    recent_activity = activity[:10]

    return jsonify({
        "stats": stats,
        "active_projects": serialize_list(active_projects),
        "recent_offers": serialize_list(recent_offers),
        "pending_proposals": serialize_list(pending_proposals),
        "recent_activity": recent_activity
    }), 200

@client_bp.route('/projects', methods=['GET'])
@client_required
def get_projects(current_user):
    client_id = str(current_user["_id"])
    status = request.args.get('status', 'all').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = {"client_id": client_id}
    if status != 'all':
        query["status"] = status
        
    total = mongo.db.projects.count_documents(query)
    projects = list(mongo.db.projects.find(query).sort("created_at", -1).skip((page - 1) * per_page).limit(per_page))
    
    for p in projects:
        freelancer = mongo.db.users.find_one({"_id": ObjectId(p["freelancer_id"])})
        if freelancer:
            p["freelancer"] = {
                "id": str(freelancer["_id"]),
                "full_name": freelancer.get("full_name"),
                "avatar_initials": freelancer.get("full_name", "?")[0].upper() if freelancer.get("full_name") else "?"
            }
            prof = mongo.db.freelancer_profiles.find_one({"user_id": p["freelancer_id"]})
            if prof: p["freelancer"]["rating"] = prof.get("avg_rating", 0)
        
        offer = mongo.db.offers.find_one({"_id": ObjectId(p["offer_id"])})
        if offer:
            p["offer"] = serialize(offer)
            
    return jsonify({
        "projects": serialize_list(projects),
        "total": total,
        "page": page,
        "per_page": per_page
    }), 200

@client_bp.route('/projects/<project_id>', methods=['GET'])
@client_required
def get_project(current_user, project_id):
    client_id = str(current_user["_id"])
    project = mongo.db.projects.find_one({"_id": ObjectId(project_id), "client_id": client_id})
    if not project:
        return jsonify({"error": "Project not found"}), 404
        
    freelancer = mongo.db.users.find_one({"_id": ObjectId(project["freelancer_id"])})
    if freelancer:
        project["freelancer"] = {
            "id": str(freelancer["_id"]),
            "full_name": freelancer.get("full_name"),
            "email": freelancer.get("email"),
            "avatar_initials": freelancer.get("full_name", "?")[0].upper() if freelancer.get("full_name") else "?"
        }
        prof = mongo.db.freelancer_profiles.find_one({"user_id": project["freelancer_id"]})
        if prof: project["freelancer"]["rating"] = prof.get("avg_rating", 0)
        
    offer = mongo.db.offers.find_one({"_id": ObjectId(project["offer_id"])})
    if offer:
        project["offer"] = serialize(offer)
        
    # Get messages
    messages = list(mongo.db.messages.find({"project_id": project_id}).sort("created_at", 1))
    
    return jsonify({
        "project": serialize(project),
        "messages": serialize_list(messages)
    }), 200
