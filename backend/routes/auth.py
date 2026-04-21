from flask import Blueprint, request, jsonify
import jwt
import datetime
from functools import wraps

from models import db, User, RoleEnum, bcrypt
from config import Config

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def token_required(f):
    """Decorator to protect routes with JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)
    return decorated


def generate_token(user):
    """Generate a JWT access token for a user."""
    payload = {
        'user_id': user.id,
        'email': user.email,
        'role': user.role.value,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES),
        'iat': datetime.datetime.now(datetime.timezone.utc),
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'client')

    # Validation
    if not full_name:
        return jsonify({'error': 'Full name is required'}), 400
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    # Check if role is valid
    try:
        role_enum = RoleEnum(role)
    except ValueError:
        return jsonify({'error': 'Invalid role. Must be freelancer, client, or admin'}), 400

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    # Create user
    user = User(
        full_name=full_name,
        email=email,
        role=role_enum,
        is_approved=(role_enum != RoleEnum.freelancer),  # Freelancers need approval
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Seed sample notifications for the new user
    from routes.notifications import seed_notifications_for_user
    seed_notifications_for_user(user)

    token = generate_token(user)

    return jsonify({
        'access_token': token,
        'user': user.to_dict(),
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate a user and return a JWT token."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = generate_token(user)

    return jsonify({
        'access_token': token,
        'user': user.to_dict(),
    }), 200


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_me(current_user):
    """Return the current authenticated user."""
    return jsonify({'user': current_user.to_dict()}), 200
