from flask import Blueprint, request, jsonify
from models import db, Review, User
from routes.auth import token_required

reviews_bp = Blueprint('reviews', __name__, url_prefix='/api')

@reviews_bp.route('/reviews', methods=['POST'])
@token_required
def create_review(current_user):
    """Submit a review."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    target_id = data.get('target_user_id')
    rating = data.get('rating')
    comment = data.get('comment', '').strip()

    if not target_id or not rating or not comment:
        return jsonify({'error': 'Missing required fields'}), 400

    if current_user.id == target_id:
        return jsonify({'error': 'Cannot review yourself'}), 400

    try:
        rating_int = int(rating)
        if rating_int < 1 or rating_int > 5:
            raise ValueError()
    except ValueError:
        return jsonify({'error': 'Rating must be integer 1-5'}), 400

    review = Review(
        reviewer_id=current_user.id,
        target_id=target_id,
        rating=rating_int,
        comment=comment
    )
    db.session.add(review)
    db.session.commit()

    return jsonify({'review': review.to_dict()}), 201

@reviews_bp.route('/users/<int:user_id>/reviews', methods=['GET'])
def get_user_reviews(user_id):
    """List reviews for a user."""
    reviews = Review.query.filter_by(target_id=user_id).order_by(Review.created_at.desc()).all()
    return jsonify({'reviews': [r.to_dict() for r in reviews]}), 200
