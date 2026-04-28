from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import datetime
from bson import ObjectId

from app import mongo, serialize, serialize_list

reviews_bp = Blueprint('reviews', __name__, url_prefix='/api')

@reviews_bp.route('/reviews', methods=['POST'])
@jwt_required()
def create_review():
    """Submit a review."""
    user_id = get_jwt_identity()
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    target_id = data.get('target_user_id')
    rating = data.get('rating')
    comment = data.get('comment', '').strip()

    if not target_id or not rating or not comment:
        return jsonify({'error': 'Missing required fields'}), 400

    if user_id == target_id:
        return jsonify({'error': 'Cannot review yourself'}), 400

    try:
        rating_int = int(rating)
        if rating_int < 1 or rating_int > 5:
            raise ValueError()
    except ValueError:
        return jsonify({'error': 'Rating must be integer 1-5'}), 400

    review_doc = {
        "reviewer_id": user_id,
        "target_id": target_id,
        "rating": rating_int,
        "comment": comment,
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    
    result = mongo.db.reviews.insert_one(review_doc)
    review_doc["_id"] = result.inserted_id

    # Populate reviewer data
    reviewer = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    review_doc["reviewer"] = serialize(reviewer) if reviewer else None

    return jsonify({'review': serialize(review_doc)}), 201

@reviews_bp.route('/users/<target_user_id>/reviews', methods=['GET'])
def get_user_reviews(target_user_id):
    """List reviews for a user."""
    reviews = list(mongo.db.reviews.find({"target_id": target_user_id}).sort("created_at", -1))
    
    for r in reviews:
        reviewer = mongo.db.users.find_one({"_id": ObjectId(r["reviewer_id"])})
        r["reviewer"] = serialize(reviewer) if reviewer else None
        
    return jsonify({'reviews': serialize_list(reviews)}), 200
