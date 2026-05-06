from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import datetime
from bson import ObjectId
import secrets
import os

from app import mongo, serialize, bcrypt

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _slugify_name(value: str) -> str:
    base = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    while "--" in base:
        base = base.replace("--", "-")
    return base or "user"


def _generate_unique_username(full_name: str) -> str:
    base = _slugify_name(full_name)
    username = base
    suffix = 1
    while mongo.db.users.find_one({"username": username}):
        suffix += 1
        username = f"{base}-{suffix}"
    return username

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data: return jsonify({'error': 'No data provided'}), 400

    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'client')
    interests = data.get('interests', [])

    if not full_name: return jsonify({'error': 'Full name is required'}), 400
    if not email: return jsonify({'error': 'Email is required'}), 400
    if not password or len(password) < 6: return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if role not in ['freelancer', 'client', 'admin']: return jsonify({'error': 'Invalid role. Must be freelancer, client, or admin'}), 400
    if interests and (not isinstance(interests, list) or any(not isinstance(i, str) for i in interests)):
        return jsonify({'error': 'Interests must be an array of strings'}), 400

    if mongo.db.users.find_one({"email": email}):
        return jsonify({'error': 'Email already registered'}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user_doc = {
        "full_name": full_name,
        "username": _generate_unique_username(full_name),
        "email": email,
        "password_hash": hashed_password,
        "role": role,
        "is_approved": (role != 'freelancer'),
        "status": "active",
        "onboarding_complete": False,
        "preferences": {},
        "interests": [i.strip() for i in interests if isinstance(i, str) and i.strip()],
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }

    result = mongo.db.users.insert_one(user_doc)
    inserted_id = str(result.inserted_id)
    user_doc["_id"] = result.inserted_id

    # Seed sample notifications for the new user
    from routes.notifications import seed_notifications_for_user
    seed_notifications_for_user(user_doc)

    token = create_access_token(identity=inserted_id)
    return jsonify({
        'access_token': token,
        'user': serialize(user_doc)
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data: return jsonify({'error': 'No data provided'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password: return jsonify({'error': 'Email and password are required'}), 400

    user = mongo.db.users.find_one({"email": email})
    if not user or not bcrypt.check_password_hash(user["password_hash"], password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if user.get("status") == "banned":
        return jsonify({'error': 'Your account has been banned.'}), 403

    # update last_login_at
    mongo.db.users.update_one({"_id": user["_id"]}, {"$set": {"last_login_at": datetime.datetime.now(datetime.timezone.utc)}})

    token = create_access_token(identity=str(user["_id"]))
    return jsonify({
        'access_token': token,
        'user': serialize(user)
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': serialize(current_user)}), 200


# ════════════════════════════════════════════════════════════════
# PASSWORD RESET & EMAIL VERIFICATION
# ════════════════════════════════════════════════════════════════

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Generate and send password reset token"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    user = mongo.db.users.find_one({'email': email})
    if not user:
        # Don't reveal if email exists for security
        return jsonify({'message': 'If email exists, reset link has been sent'}), 200
    
    # Generate secure reset token
    reset_token = secrets.token_urlsafe(32)
    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    
    # Store reset token
    mongo.db.password_resets.insert_one({
        'user_id': user['_id'],
        'token': reset_token,
        'expires_at': expires,
        'used': False,
        'created_at': datetime.datetime.now(datetime.timezone.utc)
    })
    
    # In production, send email with reset link
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:4200')
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    
    # TODO: Implement email sending
    print(f"Password reset link: {reset_link}")
    
    return jsonify({'message': 'If email exists, reset link has been sent'}), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using valid token"""
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('password')
    
    if not token or not new_password:
        return jsonify({'error': 'Token and password are required'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    # Verify token is valid and not expired
    reset = mongo.db.password_resets.find_one({
        'token': token,
        'used': False,
        'expires_at': {'$gt': datetime.datetime.now(datetime.timezone.utc)}
    })
    
    if not reset:
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    # Update password
    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    mongo.db.users.update_one(
        {'_id': reset['user_id']},
        {'$set': {'password_hash': hashed_password}}
    )
    
    # Mark token as used
    mongo.db.password_resets.update_one(
        {'_id': reset['_id']},
        {'$set': {'used': True}}
    )
    
    return jsonify({'message': 'Password reset successful'}), 200


@auth_bp.route('/send-verification-email', methods=['POST'])
@jwt_required()
def send_verification_email():
    """Send email verification token"""
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.get('email_verified'):
        return jsonify({'message': 'Email already verified'}), 200
    
    # Generate verification token
    verify_token = secrets.token_urlsafe(32)
    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    
    mongo.db.email_verifications.insert_one({
        'user_id': user['_id'],
        'email': user['email'],
        'token': verify_token,
        'expires_at': expires,
        'verified': False,
        'created_at': datetime.datetime.now(datetime.timezone.utc)
    })
    
    # In production, send verification email
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:4200')
    verify_link = f"{frontend_url}/verify-email?token={verify_token}"
    
    print(f"Email verification link: {verify_link}")
    
    return jsonify({'message': 'Verification email sent'}), 200


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify email using token"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'error': 'Token is required'}), 400
    
    verification = mongo.db.email_verifications.find_one({
        'token': token,
        'verified': False,
        'expires_at': {'$gt': datetime.datetime.now(datetime.timezone.utc)}
    })
    
    if not verification:
        return jsonify({'error': 'Invalid or expired verification token'}), 400
    
    # Mark email as verified
    mongo.db.users.update_one(
        {'_id': verification['user_id']},
        {'$set': {'email_verified': True}}
    )
    
    mongo.db.email_verifications.update_one(
        {'_id': verification['_id']},
        {'$set': {'verified': True}}
    )
    
    return jsonify({'message': 'Email verified successfully'}), 200


# ════════════════════════════════════════════════════════════════
# TWO-FACTOR AUTHENTICATION
# ════════════════════════════════════════════════════════════════

@auth_bp.route('/2fa/setup', methods=['POST'])
@jwt_required()
def setup_2fa():
    """Generate 2FA secret and QR code"""
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        import pyotp
    except ImportError:
        return jsonify({'error': '2FA not configured on server'}), 500
    
    # Generate secret
    secret = pyotp.random_base32()
    
    # Generate QR code URI
    totp = pyotp.TOTP(secret)
    qr_uri = totp.provisioning_uri(
        name=user['email'],
        issuer_name='FreelanceHub'
    )
    
    # Store temporary secret (not yet enabled)
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {
            'twofa_secret_temp': secret,
            'twofa_enabled': False
        }}
    )
    
    return jsonify({
        'qr_uri': qr_uri,
        'secret': secret
    }), 200


@auth_bp.route('/2fa/verify', methods=['POST'])
@jwt_required()
def verify_2fa():
    """Verify 2FA code and enable 2FA"""
    user_id = get_jwt_identity()
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({'error': 'Code is required'}), 400
    
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user or not user.get('twofa_secret_temp'):
        return jsonify({'error': 'No 2FA setup in progress'}), 400
    
    try:
        import pyotp
    except ImportError:
        return jsonify({'error': '2FA not configured on server'}), 500
    
    # Verify code
    totp = pyotp.TOTP(user['twofa_secret_temp'])
    if not totp.verify(code):
        return jsonify({'error': 'Invalid verification code'}), 400
    
    # Enable 2FA
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {
            '$set': {
                'twofa_secret': user['twofa_secret_temp'],
                'twofa_enabled': True
            },
            '$unset': {'twofa_secret_temp': ''}
        }
    )
    
    return jsonify({'message': '2FA enabled successfully'}), 200


@auth_bp.route('/2fa/disable', methods=['POST'])
@jwt_required()
def disable_2fa():
    """Disable 2FA"""
    user_id = get_jwt_identity()
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({'error': 'Code is required'}), 400
    
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user or not user.get('twofa_enabled'):
        return jsonify({'error': '2FA not enabled'}), 400
    
    try:
        import pyotp
    except ImportError:
        return jsonify({'error': '2FA not configured on server'}), 500
    
    # Verify code before disabling
    totp = pyotp.TOTP(user['twofa_secret'])
    if not totp.verify(code):
        return jsonify({'error': 'Invalid verification code'}), 400
    
    # Disable 2FA
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {
            '$set': {'twofa_enabled': False},
            '$unset': {'twofa_secret': ''}
        }
    )
    
    return jsonify({'message': '2FA disabled'}), 200
