from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import datetime
from bson import ObjectId

from app import mongo, serialize, serialize_list

follow_bp = Blueprint('follow', __name__, url_prefix='/api/follow')

@follow_bp.route('/<user_id>', methods=['POST'])
@jwt_required()
def toggle_follow(user_id):
    """Toggle follow/unfollow for a user."""
    follower_id = get_jwt_identity()
    if follower_id == user_id:
        return jsonify({'error': 'Cannot follow yourself'}), 400

    target = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not target:
        return jsonify({'error': 'User not found'}), 404

    existing = mongo.db.follows.find_one(
        {"follower_id": follower_id, "following_id": user_id}
    )

    if existing:
        mongo.db.follows.delete_one({"_id": existing["_id"]})
        new_count = mongo.db.follows.count_documents({"following_id": user_id})
        return jsonify({"action": "unfollowed", "follower_count": new_count}), 200
    else:
        mongo.db.follows.insert_one({
            "follower_id": follower_id,
            "following_id": user_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc)
        })
        new_count = mongo.db.follows.count_documents({"following_id": user_id})
        return jsonify({"action": "followed", "follower_count": new_count}), 200


@follow_bp.route('/<user_id>/followers', methods=['GET'])
def get_followers(user_id):
    """Return the list of followers for a user."""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    total = mongo.db.follows.count_documents({"following_id": user_id})
    follows = list(mongo.db.follows.find({"following_id": user_id})
                   .sort("created_at", -1)
                   .skip((page - 1) * limit)
                   .limit(limit))
    followers = []
    for f in follows:
        u = mongo.db.users.find_one({"_id": ObjectId(f["follower_id"])})
        if u:
            followers.append({
                "id": str(u["_id"]),
                "full_name": u.get("full_name"),
                "avatar_initials": u.get("full_name", "?")[0].upper(),
                "role": u.get("role"),
                "followed_at": f.get("created_at")
            })
    return jsonify({
        "data": followers, 
        "meta": {
            "page": page,
            "total": total,
            "has_more": (page * limit) < total
        }
    }), 200


@follow_bp.route('/feed', methods=['GET'])
@jwt_required()
def get_following_feed():
    """Return recent updates from freelancers the current user follows."""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    # Get IDs of users this person follows
    following = list(mongo.db.follows.find({"follower_id": user_id}))
    following_ids = [f["following_id"] for f in following]

    if not following_ids:
        return jsonify({"data": [], "meta": {"page": page, "total": 0, "has_more": False}}), 200

    feed = []

    # Recent completed projects by followed freelancers
    recent_projects = list(mongo.db.projects.find({
        "freelancer_id": {"$in": following_ids},
        "status": {"$in": ["active", "completed"]}
    }).sort("started_at", -1).limit(limit * page))

    for p in recent_projects:
        freelancer = mongo.db.users.find_one({"_id": ObjectId(p["freelancer_id"])})
        if not freelancer:
            continue
        feed.append({
            "type": "project",
            "freelancer": {
                "id": str(freelancer["_id"]),
                "full_name": freelancer.get("full_name"),
                "avatar_initials": freelancer.get("full_name", "?")[0].upper()
            },
            "title": p.get("title"),
            "status": p.get("status"),
            "description": f"{freelancer.get('full_name')} travaille sur \"{p.get('title')}\"" if p.get("status") == "active" else f"{freelancer.get('full_name')} a terminé \"{p.get('title')}\"",
            "date": p.get("started_at") or p.get("completed_at"),
            "project_id": str(p["_id"])
        })

    # Recent services by followed freelancers
    recent_services = list(mongo.db.services.find({
        "freelancer_id": {"$in": following_ids},
        "approval_status": "approved"
    }).sort("created_at", -1).limit(5 * page))

    for s in recent_services:
        freelancer = mongo.db.users.find_one({"_id": ObjectId(s["freelancer_id"])})
        if not freelancer:
            continue
        feed.append({
            "type": "service",
            "freelancer": {
                "id": str(freelancer["_id"]),
                "full_name": freelancer.get("full_name"),
                "avatar_initials": freelancer.get("full_name", "?")[0].upper()
            },
            "title": s.get("title"),
            "description": f"{freelancer.get('full_name')} propose \"{s.get('title')}\"",
            "date": s.get("created_at"),
            "service_id": str(s["_id"])
        })

    # Sort by date descending
    feed.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    total_feed_items = len(feed)
    start_idx = (page - 1) * limit
    feed_page = feed[start_idx:start_idx + limit]

    return jsonify({
        "data": serialize_list(feed_page), 
        "meta": {
            "page": page,
            "total": total_feed_items,
            "has_more": (page * limit) < total_feed_items
        }
    }), 200
