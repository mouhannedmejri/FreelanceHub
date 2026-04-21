import os
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
from models import db, User, FreelancerProfile
from routes.auth import token_required

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


@users_bp.route('/profile', methods=['GET'])
@token_required
def get_own_profile(current_user):
    """Return the full profile for the current user."""
    profile = FreelancerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile and current_user.role.value == 'freelancer':
        profile = FreelancerProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()

    return jsonify({
        'user': current_user.to_dict(),
        'profile': profile.to_dict() if profile else None,
    }), 200


@users_bp.route('/<int:user_id>/profile', methods=['GET'])
def get_profile(user_id):
    """Return the full profile for a user."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    profile = FreelancerProfile.query.filter_by(user_id=user_id).first()
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
    from models import Certification, PortfolioItem

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    profile = FreelancerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = FreelancerProfile(user_id=current_user.id)
        db.session.add(profile)

    updatable_fields = ['bio', 'title', 'hourly_rate', 'location', 'phone', 'skills']
    for field in updatable_fields:
        if field in data:
            setattr(profile, field, data[field])

    if 'certifications' in data:
        # Delete old certs
        Certification.query.filter_by(user_id=current_user.id).delete()
        for cert_data in data['certifications']:
            cert = Certification(
                user_id=current_user.id,
                name=cert_data.get('name', ''),
                issuer=cert_data.get('issuer', ''),
                year=cert_data.get('year', '')
            )
            db.session.add(cert)

    if 'portfolio' in data:
        # Delete old portfolio items
        PortfolioItem.query.filter_by(user_id=current_user.id).delete()
        for item_data in data['portfolio']:
            item = PortfolioItem(
                user_id=current_user.id,
                title=item_data.get('title', ''),
                description=item_data.get('description', ''),
                skills=item_data.get('skills', []),
                image_url=item_data.get('image_url', '')
            )
            db.session.add(item)

    db.session.commit()

    return jsonify({
        'user': current_user.to_dict(),
        'profile': profile.to_dict(),
    }), 200


@users_bp.route('/profile/cv', methods=['POST'])
@token_required
def upload_cv(current_user):
    """Upload a CV PDF (max 5 MB) for the current user."""
    # Check if JSON with base64 is sent
    if request.is_json:
        data = request.get_json()
        if 'cv_base64' in data:
            # Handle base64 simulated upload
            profile = FreelancerProfile.query.filter_by(user_id=current_user.id).first()
            if not profile:
                profile = FreelancerProfile(user_id=current_user.id)
                db.session.add(profile)
            
            profile.cv_filename = data.get('filename', 'cv.pdf')
            # Simulated size calculation
            profile.cv_size = len(data['cv_base64']) * 3 // 4 
            db.session.commit()
            return jsonify({'user': current_user.to_dict(), 'profile': profile.to_dict()}), 200

    if 'cv' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['cv']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed'}), 400

    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(f"cv_{current_user.id}_{file.filename}")
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    profile = FreelancerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = FreelancerProfile(user_id=current_user.id)
        db.session.add(profile)

    profile.cv_filename = filename
    profile.cv_size = os.path.getsize(filepath)
    db.session.commit()

    return jsonify({
        'user': current_user.to_dict(),
        'profile': profile.to_dict(),
    }), 200


@users_bp.route('/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    """Serve an uploaded file (e.g. CV PDF)."""
    return send_from_directory(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename)
