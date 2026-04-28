from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import datetime
from bson import ObjectId

from app import mongo, serialize, bcrypt

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data: return jsonify({'error': 'No data provided'}), 400

    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'client')

    if not full_name: return jsonify({'error': 'Full name is required'}), 400
    if not email: return jsonify({'error': 'Email is required'}), 400
    if not password or len(password) < 6: return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if role not in ['freelancer', 'client', 'admin']: return jsonify({'error': 'Invalid role. Must be freelancer, client, or admin'}), 400

    if mongo.db.users.find_one({"email": email}):
        return jsonify({'error': 'Email already registered'}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user_doc = {
        "full_name": full_name,
        "email": email,
        "password_hash": hashed_password,
        "role": role,
        "is_approved": (role != 'freelancer'),
        "status": "active",
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
