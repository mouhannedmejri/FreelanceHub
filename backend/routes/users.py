import os
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from app import mongo, serialize

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
    """Return the full profile for a user."""
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    profile = get_or_create_profile(user_id, user.get("role"))

    return jsonify({
        'user': serialize(user),
        'profile': serialize(profile) if profile else None,
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
