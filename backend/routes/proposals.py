from flask import Blueprint, request, jsonify
from models import db, Proposal, Offer, ProposalStatusEnum, OfferStatusEnum
from routes.auth import token_required

proposals_bp = Blueprint('proposals', __name__, url_prefix='/api/proposals')

@proposals_bp.route('/<int:proposal_id>', methods=['PATCH'])
@token_required
def update_proposal_status(current_user, proposal_id):
    """Client accepts or rejects a proposal."""
    proposal = Proposal.query.get(proposal_id)
    if not proposal:
        return jsonify({'error': 'Proposal not found'}), 404

    offer = proposal.offer
    if offer.client_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    status_str = data.get('status')
    if status_str not in ['accepted', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400

    try:
        new_status = ProposalStatusEnum(status_str)
    except ValueError:
        return jsonify({'error': 'Invalid status'}), 400

    proposal.status = new_status
    if new_status == ProposalStatusEnum.accepted:
        offer.status = OfferStatusEnum.closed

    db.session.commit()
    return jsonify({'proposal': proposal.to_dict()}), 200
