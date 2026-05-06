import os
import datetime
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from bson import ObjectId

from app import mongo, serialize

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


def _default_freelancer_profile(user_id):
    return {
        "user_id": user_id,
        "bio": "",
        "title": "",
        "hourly_rate": 0,
        "location": "",
        "phone": "",
        "skills": [],
        "certifications": [],
        "portfolio": [],  # legacy field
        "portfolio_projects": [],
        "skills_endorsed": [],
        "video_intro_url": "",
        "availability_status": "available",
        "languages": [],
        "work_experience": [],
        "education": [],
        "cv_filename": "",
        "cv_size": 0,
        "avg_rating": 0.0,
        "total_reviews": 0,
    }


def get_or_create_profile(user_id, role):
    profile = mongo.db.freelancer_profiles.find_one({"user_id": user_id})
    if not profile and role == 'freelancer':
        profile = _default_freelancer_profile(user_id)
        mongo.db.freelancer_profiles.insert_one(profile)
    return profile


def _compute_profile_completion(profile):
    if not profile:
        return {"completion_percentage": 0, "boost_suggestions": ["Complete your freelancer profile basics."]}

    checks = [
        ("bio", bool(profile.get("bio"))),
        ("title", bool(profile.get("title"))),
        ("skills", len(profile.get("skills", [])) >= 3),
        ("portfolio_projects", len(profile.get("portfolio_projects", [])) >= 1),
        ("certifications", len(profile.get("certifications", [])) >= 1),
        ("languages", len(profile.get("languages", [])) >= 1),
        ("work_experience", len(profile.get("work_experience", [])) >= 1),
        ("education", len(profile.get("education", [])) >= 1),
        ("video_intro_url", bool(profile.get("video_intro_url"))),
        ("hourly_rate", float(profile.get("hourly_rate") or 0) > 0),
    ]

    completed = [name for name, ok in checks if ok]
    missing = [name for name, ok in checks if not ok]
    percentage = int((len(completed) / len(checks)) * 100)

    suggestions_map = {
        "bio": "Add a professional bio.",
        "title": "Set a clear professional title.",
        "skills": "Add at least 3 core skills.",
        "portfolio_projects": "Add at least 1 portfolio project.",
        "certifications": "Add relevant certifications.",
        "languages": "Add your spoken languages.",
        "work_experience": "Add work experience entries.",
        "education": "Add your education background.",
        "video_intro_url": "Add a short video introduction.",
        "hourly_rate": "Set your hourly rate.",
    }

    return {
        "completion_percentage": percentage,
        "boost_suggestions": [suggestions_map[m] for m in missing[:5]],
    }


@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_own_profile():
    user_id = get_jwt_identity()
    current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    profile = get_or_create_profile(user_id, current_user.get("role"))

    completion = _compute_profile_completion(profile)
    return jsonify({
        'user': serialize(current_user),
        'profile': serialize(profile) if profile else None,
        **completion,
    }), 200


@users_bp.route('/<user_id>/profile', methods=['GET'])
def get_profile(user_id):
    try:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400
    if not user:
        return jsonify({'error': 'User not found'}), 404

    profile = get_or_create_profile(user_id, user.get("role"))

    user.pop("password_hash", None)
    user.pop("email", None)
    user.pop("preferences", None)
    user.pop("ban_reason", None)

    follower_count = mongo.db.follows.count_documents({"following_id": user_id})

    is_following = False
    try:
        verify_jwt_in_request(optional=True)
        viewer_id = get_jwt_identity()
        if viewer_id and viewer_id != user_id:
            is_following = mongo.db.follows.count_documents({"follower_id": viewer_id, "following_id": user_id}) > 0
    except Exception:
        pass

    completed_count = mongo.db.projects.count_documents({"freelancer_id": user_id, "status": "completed"})
    pipeline = [
        {"$match": {"freelancer_id": user_id, "status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$budget"}}}
    ]
    earnings_res = list(mongo.db.projects.aggregate(pipeline))
    total_earnings = earnings_res[0]["total"] if earnings_res else 0

    badges = []
    avg_rating = profile.get("avg_rating", 0) if profile else 0
    total_reviews = profile.get("total_reviews", 0) if profile else 0
    if avg_rating >= 4.8 and total_reviews >= 5:
        badges.append("Top Rated")
    if completed_count >= 3:
        badges.append("Fast Reply")

    availability = "Offline"
    last_login = user.get("last_login_at")
    if last_login:
        if last_login.tzinfo is None:
            last_login = last_login.replace(tzinfo=datetime.timezone.utc)
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = (now - last_login).total_seconds()
        if diff < 300:
            availability = "Online now"
        elif diff < 7200:
            availability = "Response in 2h"
        elif diff < 86400:
            availability = "Response today"

    completion = _compute_profile_completion(profile)
    share_url = f"/freelancer/{user.get('username')}" if user.get("username") else ""

    return jsonify({
        'user': serialize(user),
        'profile': serialize(profile) if profile else None,
        'follower_count': follower_count,
        'is_following': is_following,
        'badges': badges,
        'availability': availability,
        'share_url': share_url,
        **completion,
        'stats': {
            'earnings': total_earnings,
            'hired': completed_count,
            'rating': avg_rating,
            'reviews': total_reviews,
            'followers': follower_count
        }
    }), 200


@users_bp.route('/freelancer/<username>', methods=['GET'])
def get_profile_by_username(username):
    normalized = (username or '').strip().lower()
    user = mongo.db.users.find_one({"username": normalized, "role": "freelancer"})
    if not user:
        return jsonify({'error': 'Freelancer not found'}), 404
    return get_profile(str(user["_id"]))


@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    profile = get_or_create_profile(user_id, current_user.get("role"))

    update_data = {}
    updatable_fields = [
        'bio', 'title', 'hourly_rate', 'location', 'phone', 'skills',
        'certifications', 'portfolio', 'portfolio_projects', 'skills_endorsed',
        'video_intro_url', 'availability_status', 'languages', 'work_experience', 'education'
    ]
    for field in updatable_fields:
        if field in data:
            update_data[field] = data[field]

    if update_data:
        mongo.db.freelancer_profiles.update_one({"user_id": user_id}, {"$set": update_data})
        profile.update(update_data)

    completion = _compute_profile_completion(profile)
    return jsonify({'user': serialize(current_user), 'profile': serialize(profile), **completion}), 200


@users_bp.route('/onboarding', methods=['PUT'])
@jwt_required()
def update_onboarding_preferences():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    preferences = data.get('preferences')
    interests = data.get('interests', [])
    onboarding_complete = bool(data.get('onboarding_complete', False))

    if not isinstance(preferences, dict):
        return jsonify({'error': 'preferences must be an object'}), 400
    if interests and (not isinstance(interests, list) or any(not isinstance(i, str) for i in interests)):
        return jsonify({'error': 'interests must be an array of strings'}), 400

    set_payload = {"preferences": preferences, "onboarding_complete": onboarding_complete}
    if interests:
        set_payload["interests"] = [i.strip() for i in interests if isinstance(i, str) and i.strip()]
    mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": set_payload})
    updated_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    return jsonify({'user': serialize(updated_user)}), 200


@users_bp.route('/interests', methods=['PUT'])
@jwt_required()
def update_interests():
    user_id = get_jwt_identity()
    current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not current_user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    interests = data.get('interests', [])
    if not isinstance(interests, list) or any(not isinstance(i, str) for i in interests):
        return jsonify({'error': 'interests must be an array of strings'}), 400

    clean_interests = [i.strip() for i in interests if isinstance(i, str) and i.strip()]
    mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"interests": clean_interests}})
    updated_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    return jsonify({"user": serialize(updated_user)}), 200


@users_bp.route('/profile/cv', methods=['POST'])
@jwt_required()
def upload_cv():
    user_id = get_jwt_identity()
    current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    if request.is_json:
        data = request.get_json()
        if 'cv_base64' in data:
            profile = get_or_create_profile(user_id, current_user.get("role"))
            cv_filename = data.get('filename', 'cv.pdf')
            cv_size = len(data['cv_base64']) * 3 // 4
            mongo.db.freelancer_profiles.update_one({"user_id": user_id}, {"$set": {"cv_filename": cv_filename, "cv_size": cv_size}})
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
    mongo.db.freelancer_profiles.update_one({"user_id": user_id}, {"$set": {"cv_filename": filename, "cv_size": cv_size}})
    profile["cv_filename"] = filename
    profile["cv_size"] = cv_size

    return jsonify({'user': serialize(current_user), 'profile': serialize(profile)}), 200


@users_bp.route('/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    return send_from_directory(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename)


@users_bp.route('/uploads/path/<path:filename>', methods=['GET'])
def serve_upload_path(filename):
    return send_from_directory(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename)


# ════════════════════════════════════════════════════════════════
# ACCOUNT MANAGEMENT
# ════════════════════════════════════════════════════════════════

@users_bp.route('/deactivate', methods=['POST'])
@jwt_required()
def deactivate_account():
    """Temporarily deactivate user account"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    reason = data.get('reason', '')
    
    # Soft delete - mark as deactivated
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {
            '$set': {
                'is_active': False,
                'deactivated_at': datetime.datetime.now(datetime.timezone.utc),
                'deactivation_reason': reason,
                'status': 'inactive'
            }
        }
    )
    
    # Log for analytics
    mongo.db.account_actions.insert_one({
        'user_id': ObjectId(user_id),
        'action': 'deactivate',
        'reason': reason,
        'timestamp': datetime.datetime.now(datetime.timezone.utc)
    })
    
    return jsonify({'message': 'Account deactivated. You can reactivate within 30 days.'}), 200


@users_bp.route('/reactivate', methods=['POST'])
@jwt_required()
def reactivate_account():
    """Reactivate a deactivated account"""
    user_id = get_jwt_identity()
    
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {
            '$set': {
                'is_active': True,
                'status': 'active'
            },
            '$unset': {
                'deactivated_at': '',
                'deactivation_reason': ''
            }
        }
    )
    
    mongo.db.account_actions.insert_one({
        'user_id': ObjectId(user_id),
        'action': 'reactivate',
        'timestamp': datetime.datetime.now(datetime.timezone.utc)
    })
    
    return jsonify({'message': 'Account reactivated'}), 200


@users_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def delete_account():
    """Permanently delete user account after validation"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    password = data.get('password')
    
    if not password:
        return jsonify({'error': 'Password is required to delete account'}), 400
    
    # Verify password
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    from app import bcrypt
    if not bcrypt.check_password_hash(user.get('password_hash', ''), password):
        return jsonify({'error': 'Invalid password'}), 401
    
    # Check for active projects
    active_projects = mongo.db.projects.count_documents({
        '$or': [
            {'client_id': ObjectId(user_id)},
            {'freelancer_id': ObjectId(user_id)}
        ],
        'status': {'$in': ['in_progress', 'pending', 'quoted']}
    })
    
    if active_projects > 0:
        return jsonify({'error': 'Complete or cancel all active projects before deleting account'}), 400
    
    # Anonymize user data instead of true delete for audit trail
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {
            '$set': {
                'email': f'deleted_{user_id}@deleted.local',
                'full_name': 'Deleted User',
                'is_deleted': True,
                'deleted_at': datetime.datetime.now(datetime.timezone.utc),
                'status': 'deleted'
            },
            '$unset': {
                'phone': '',
                'profile_picture': '',
                'password_hash': '',
                'twofa_secret': '',
                'email_verified': ''
            }
        }
    )
    
    # Log deletion
    mongo.db.account_actions.insert_one({
        'user_id': ObjectId(user_id),
        'action': 'delete',
        'timestamp': datetime.datetime.now(datetime.timezone.utc)
    })
    
    return jsonify({'message': 'Account deleted successfully'}), 200


# ════════════════════════════════════════════════════════════════
# PRIVACY SETTINGS
# ════════════════════════════════════════════════════════════════

@users_bp.route('/privacy-settings', methods=['GET'])
@jwt_required()
def get_privacy_settings():
    """Get user privacy settings"""
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    default_settings = {
        'show_email': False,
        'show_phone': False,
        'show_location': True,
        'show_earnings': False,
        'allow_messages_from': 'verified_only',  # 'anyone', 'verified_only', 'connections_only'
        'show_online_status': True,
        'profile_visibility': 'public'  # 'public', 'logged_in_only', 'private'
    }
    
    settings = user.get('privacy_settings', default_settings)
    return jsonify({'privacy_settings': settings}), 200


@users_bp.route('/privacy-settings', methods=['PUT'])
@jwt_required()
def update_privacy_settings():
    """Update user privacy settings"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Settings data is required'}), 400
    
    # Validate settings
    valid_message_options = ['anyone', 'verified_only', 'connections_only']
    valid_visibility_options = ['public', 'logged_in_only', 'private']
    
    if 'allow_messages_from' in data and data['allow_messages_from'] not in valid_message_options:
        return jsonify({'error': 'Invalid allow_messages_from value'}), 400
    
    if 'profile_visibility' in data and data['profile_visibility'] not in valid_visibility_options:
        return jsonify({'error': 'Invalid profile_visibility value'}), 400
    
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'privacy_settings': data}}
    )
    
    return jsonify({'message': 'Privacy settings updated'}), 200


@users_bp.route('/block-user/<blocked_user_id>', methods=['POST'])
@jwt_required()
def block_user(blocked_user_id):
    """Block a user"""
    user_id = get_jwt_identity()
    
    # Validate blocked user exists
    blocked_user = mongo.db.users.find_one({'_id': ObjectId(blocked_user_id)})
    if not blocked_user:
        return jsonify({'error': 'User not found'}), 404
    
    # Add to blocked users list
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$addToSet': {'blocked_users': ObjectId(blocked_user_id)}}
    )
    
    return jsonify({'message': 'User blocked'}), 200


@users_bp.route('/unblock-user/<blocked_user_id>', methods=['POST'])
@jwt_required()
def unblock_user(blocked_user_id):
    """Unblock a user"""
    user_id = get_jwt_identity()
    
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$pull': {'blocked_users': ObjectId(blocked_user_id)}}
    )
    
    return jsonify({'message': 'User unblocked'}), 200


@users_bp.route('/blocked-users', methods=['GET'])
@jwt_required()
def get_blocked_users():
    """Get list of blocked users"""
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    blocked_ids = user.get('blocked_users', [])
    blocked_users = list(mongo.db.users.find(
        {'_id': {'$in': blocked_ids}},
        {'password_hash': 0, 'twofa_secret': 0}
    ))
    
    return jsonify({'blocked_users': [serialize(u) for u in blocked_users]}), 200


