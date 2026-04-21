import os
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
from models import db, User, FreelancerProfile
from routes.auth import token_required

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


@users_bp.route('/<int:user_id>/profile', methods=['GET'])
def get_profile(user_id):
    """Return the full profile for a user (bio, skills, portfolio, certifications)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    profile = FreelancerProfile.query.filter_by(user_id=user_id).first()

    # Auto-create a blank profile for freelancers who don't have one yet
    if not profile and user.role.value == 'freelancer':
        profile = FreelancerProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()

    return jsonify({
        'user': user.to_dict(),
        'profile': profile.to_dict() if profile else None,
    }), 200


@users_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Update the current user's freelancer profile."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    profile = FreelancerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = FreelancerProfile(user_id=current_user.id)
        db.session.add(profile)

    updatable_fields = [
        'bio', 'title', 'hourly_rate', 'location', 'phone',
        'skills', 'portfolio', 'certifications',
    ]
    for field in updatable_fields:
        if field in data:
            setattr(profile, field, data[field])

    db.session.commit()

    return jsonify({
        'user': current_user.to_dict(),
        'profile': profile.to_dict(),
    }), 200


@users_bp.route('/profile/cv', methods=['POST'])
@token_required
def upload_cv(current_user):
    """Upload a CV PDF (max 5 MB) for the current user."""
    if 'cv' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['cv']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed'}), 400

    # Ensure uploads directory exists
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(f"cv_{current_user.id}_{file.filename}")
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    # Update (or create) profile
    profile = FreelancerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = FreelancerProfile(user_id=current_user.id)
        db.session.add(profile)

    profile.cv_filename = filename
    db.session.commit()

    return jsonify({
        'user': current_user.to_dict(),
        'profile': profile.to_dict(),
    }), 200


@users_bp.route('/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    """Serve an uploaded file (e.g. CV PDF)."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
