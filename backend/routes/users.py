import os
import datetime
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from bson import ObjectId

from app import mongo, serialize, serialize_list

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

def get_or_create_profile(user_id, role):
    profile = mongo.db.freelancer_profiles.find_one({"user_id": user_id})
    if not profile and role == 'freelancer':
        profile = {
            "user_id": user_id,
            "bio": "",
            "title": "",
            "hourly_rate": 0,
            "location": "",
            "phone": "",
            "skills": [],
            "certifications": [],
            "portfolio": [],
            "cv_filename": "",
            "cv_size": 0,
            "avg_rating": 0.0,
            "total_reviews": 0
        }
        mongo.db.freelancer_profiles.insert_one(profile)
    return profile

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_own_profile():
    """Return the full profile for the current user."""
    user_id = get_jwt_identity()
    current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    
    profile = get_or_create_profile(user_id, current_user.get("role"))

    return jsonify({
        'user': serialize(current_user),
        'profile': serialize(profile) if profile else None,
    }), 200


@users_bp.route('/<user_id>/profile', methods=['GET'])
def get_profile(user_id):
    """Return the full profile for a user with badges, stats, follower info."""
    try:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400
    if not user:
        return jsonify({'error': 'User not found'}), 404

    profile = get_or_create_profile(user_id, user.get("role"))

    # Follower count
    follower_count = mongo.db.follows.count_documents({"following_id": user_id})

    # Is viewer following this user?
    is_following = False
    try:
        verify_jwt_in_request(optional=True)
        viewer_id = get_jwt_identity()
        if viewer_id and viewer_id != user_id:
            is_following = mongo.db.follows.count_documents(
                {"follower_id": viewer_id, "following_id": user_id}
            ) > 0
    except Exception:
        pass

    # Compute stats
    completed_count = mongo.db.projects.count_documents({"freelancer_id": user_id, "status": "completed"})
    pipeline = [
        {"$match": {"freelancer_id": user_id, "status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$budget"}}}
    ]
    earnings_res = list(mongo.db.projects.aggregate(pipeline))
    total_earnings = earnings_res[0]["total"] if earnings_res else 0

    # Badges
    badges = []
    avg_rating = profile.get("avg_rating", 0) if profile else 0
    total_reviews = profile.get("total_reviews", 0) if profile else 0
    if avg_rating >= 4.8 and total_reviews >= 5:
        badges.append("Top Rated")
    # Fast reply badge: placeholder logic — check if user has responded to messages quickly
    # For now: award if they have > 3 completed projects
    if completed_count >= 3:
        badges.append("Fast Reply")

    # Availability: check last_login_at
    availability = "Offline"
    last_login = user.get("last_login_at")
    if last_login:
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = (now - last_login).total_seconds()
        if diff < 300:  # 5 minutes
            availability = "Online now"
        elif diff < 7200:  # 2 hours
            availability = "Response in 2h"
        elif diff < 86400:  # 24 hours
            availability = "Response today"
        else:
            availability = "Offline"

    return jsonify({
        'user': serialize(user),
        'profile': serialize(profile) if profile else None,
        'follower_count': follower_count,
        'is_following': is_following,
        'badges': badges,
        'availability': availability,
        'stats': {
            'earnings': total_earnings,
            'hired': completed_count,
            'rating': avg_rating,
            'reviews': total_reviews,
            'followers': follower_count
        }
    }), 200


@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update the current user's freelancer profile."""
    user_id = get_jwt_identity()
    current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    profile = get_or_create_profile(user_id, current_user.get("role"))
    
    update_data = {}
    updatable_fields = ['bio', 'title', 'hourly_rate', 'location', 'phone', 'skills', 'certifications', 'portfolio']
    for field in updatable_fields:
        if field in data:
            update_data[field] = data[field]

    if update_data:
        mongo.db.freelancer_profiles.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        profile.update(update_data)

    return jsonify({
        'user': serialize(current_user),
        'profile': serialize(profile),
    }), 200


@users_bp.route('/onboarding', methods=['PUT'])
@jwt_required()
def update_onboarding_preferences():
    """Update onboarding preferences and mark onboarding complete."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    preferences = data.get('preferences')
    onboarding_complete = bool(data.get('onboarding_complete', False))

    if not isinstance(preferences, dict):
        return jsonify({'error': 'preferences must be an object'}), 400

    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"preferences": preferences, "onboarding_complete": onboarding_complete}}
    )
    updated_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    return jsonify({'user': serialize(updated_user)}), 200


@users_bp.route('/profile/cv', methods=['POST'])
@jwt_required()
def upload_cv():
    """Upload a CV PDF (max 5 MB) for the current user."""
    user_id = get_jwt_identity()
    current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    # Check if JSON with base64 is sent
    if request.is_json:
        data = request.get_json()
        if 'cv_base64' in data:
            profile = get_or_create_profile(user_id, current_user.get("role"))
            
            cv_filename = data.get('filename', 'cv.pdf')
            cv_size = len(data['cv_base64']) * 3 // 4 
            
            mongo.db.freelancer_profiles.update_one(
                {"user_id": user_id},
                {"$set": {"cv_filename": cv_filename, "cv_size": cv_size}}
            )
            profile["cv_filename"] = cv_filename
            profile["cv_size"] = cv_size
            
            return jsonify({'user': serialize(current_user), 'profile': serialize(profile)}), 200

    if 'cv' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['cv']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed'}), 400

    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(f"cv_{user_id}_{file.filename}")
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    profile = get_or_create_profile(user_id, current_user.get("role"))
    cv_size = os.path.getsize(filepath)
    
    mongo.db.freelancer_profiles.update_one(
        {"user_id": user_id},
        {"$set": {"cv_filename": filename, "cv_size": cv_size}}
    )
    profile["cv_filename"] = filename
    profile["cv_size"] = cv_size

    return jsonify({
        'user': serialize(current_user),
        'profile': serialize(profile),
    }), 200


@users_bp.route('/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    """Serve an uploaded file (e.g. CV PDF)."""
    return send_from_directory(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename)


# ─── FOLLOW SYSTEM ────────────────────────────────────────────────────

@users_bp.route('/<user_id>/follow', methods=['POST'])
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


@users_bp.route('/<user_id>/followers', methods=['GET'])
def get_followers(user_id):
    """Return the list of followers for a user."""
    follows = list(mongo.db.follows.find({"following_id": user_id}).sort("created_at", -1))
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
    return jsonify({"followers": followers, "total": len(followers)}), 200


@users_bp.route('/following-feed', methods=['GET'])
@jwt_required()
def get_following_feed():
    """Return recent updates from freelancers the current user follows."""
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 10, type=int)

    # Get IDs of users this person follows
    following = list(mongo.db.follows.find({"follower_id": user_id}))
    following_ids = [f["following_id"] for f in following]

    if not following_ids:
        return jsonify({"feed": [], "total": 0}), 200

    feed = []

    # Recent completed projects by followed freelancers
    recent_projects = list(mongo.db.projects.find({
        "freelancer_id": {"$in": following_ids},
        "status": {"$in": ["active", "completed"]}
    }).sort("started_at", -1).limit(limit))

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
    }).sort("created_at", -1).limit(5))

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
    feed = feed[:limit]

    return jsonify({"feed": serialize_list(feed), "total": len(feed)}), 200
