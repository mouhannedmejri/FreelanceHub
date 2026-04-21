from flask import Blueprint, request, jsonify
from functools import wraps
from models import db, User, Offer, Service, FreelancerProfile, RoleEnum
from routes.auth import token_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if current_user.role != RoleEnum.admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats(current_user):
    """Admin dashboard statistics."""
    total_users = User.query.count()
    freelancers = User.query.filter_by(role=RoleEnum.freelancer).count()
    clients = User.query.filter_by(role=RoleEnum.client).count()
    offers = Offer.query.count()
    services = Service.query.count()
    
    # Revenue logic placeholder (since we don't have a payments table yet)
    revenue = 15420.50 

    return jsonify({
        'total_users': total_users,
        'freelancers': freelancers,
        'clients': clients,
        'offers': offers,
        'services': services,
        'revenue': revenue
    }), 200

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users(current_user):
    """List users, optionally filtered by role."""
    role_str = request.args.get('role', '').strip()
    query = User.query
    if role_str:
        try:
            query = query.filter_by(role=RoleEnum(role_str))
        except ValueError:
            pass

    users = query.order_by(User.created_at.desc()).all()
    return jsonify({'users': [u.to_dict() for u in users]}), 200

@admin_bp.route('/users/<int:user_id>/approve', methods=['PATCH'])
@admin_required
def toggle_approve(current_user, user_id):
    """Toggle is_approved for a user (mainly freelancers)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.is_approved = not user.is_approved
    db.session.commit()
    
    return jsonify({'user': user.to_dict()}), 200
