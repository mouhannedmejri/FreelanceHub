"""Decorators for optional and role-based JWT authentication.

Usage:
    @jwt_optional
    def get_offers():
        user_id = get_jwt_identity()  # None if no JWT
        ...

    @role_required('client')
    def create_offer():
        ...
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from bson import ObjectId

from app import mongo


def jwt_optional(fn):
    """Decorator that makes JWT optional.

    - If a valid JWT is present, the request proceeds with full identity.
    - If no JWT is present, the request proceeds with `get_jwt_identity()` returning None.
    - If an invalid/expired JWT is present, it is ignored (treated as guest).
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
        except Exception:
            pass  # Invalid/expired token → treat as guest
        return fn(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """Decorator that requires JWT and checks user role.

    Usage:
        @role_required('client')
        @role_required('client', 'admin')
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception:
                return jsonify({'error': 'Authentication required'}), 401

            user_id = get_jwt_identity()
            user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return jsonify({'error': 'User not found'}), 404
            if user.get('role') not in roles:
                return jsonify({'error': f'Requires one of roles: {", ".join(roles)}'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
