from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from app import mongo, serialize

proposals_bp = Blueprint('proposals', __name__, url_prefix='/api/proposals')

@proposals_bp.route('/<proposal_id>', methods=['PATCH'])
@jwt_required()
def update_proposal_status(proposal_id):
    """Client accepts or rejects a proposal."""
    user_id = get_jwt_identity()
    
    proposal = mongo.db.proposals.find_one({"_id": ObjectId(proposal_id)})
    if not proposal:
        return jsonify({'error': 'Proposal not found'}), 404

    offer = mongo.db.offers.find_one({"_id": ObjectId(proposal["offer_id"])})
    if not offer or offer.get("client_id") != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    status_str = data.get('status')
    if status_str not in ['accepted', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400

    mongo.db.proposals.update_one(
        {"_id": ObjectId(proposal_id)},
        {"$set": {"status": status_str}}
    )
    proposal["status"] = status_str

    if status_str == 'accepted':
        mongo.db.offers.update_one(
            {"_id": ObjectId(proposal["offer_id"])},
            {"$set": {"status": "closed"}}
        )

    return jsonify({'proposal': serialize(proposal)}), 200
