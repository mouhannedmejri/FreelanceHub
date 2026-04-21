from flask import Blueprint, request, jsonify
from models import db, Offer, CategoryEnum, LocationEnum, OfferStatusEnum
from routes.auth import token_required

offers_bp = Blueprint('offers', __name__, url_prefix='/api/offers')


@offers_bp.route('/', methods=['GET'])
def get_offers():
    """Return all active offers (freelancer/visitor view), optionally filtered by search."""
    search = request.args.get('search', '').strip()

    query = Offer.query.filter_by(status=OfferStatusEnum.active)

    if search:
        like_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Offer.title.ilike(like_term),
                Offer.description.ilike(like_term),
            )
        )

    offers = query.order_by(Offer.created_at.desc()).all()
    return jsonify({
        'offers': [o.to_dict() for o in offers],
        'total': len(offers),
    }), 200


@offers_bp.route('/mine', methods=['GET'])
@token_required
def get_my_offers(current_user):
    """Return offers created by the authenticated client."""
    offers = (
        Offer.query
        .filter_by(client_id=current_user.id)
        .order_by(Offer.created_at.desc())
        .all()
    )
    return jsonify({
        'offers': [o.to_dict() for o in offers],
        'total': len(offers),
    }), 200


@offers_bp.route('/<int:offer_id>', methods=['GET'])
def get_offer(offer_id):
    """Return a single offer by ID."""
    offer = Offer.query.get(offer_id)
    if not offer:
        return jsonify({'error': 'Offer not found'}), 404
    return jsonify({'offer': offer.to_dict()}), 200


@offers_bp.route('/', methods=['POST'])
@token_required
def create_offer(current_user):
    """Create a new offer (client only)."""
    if current_user.role.value != 'client':
        return jsonify({'error': 'Only clients can create offers'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    category_str = data.get('category', '').strip()
    skills = data.get('skills', [])
    budget_min = data.get('budget_min', 0)
    budget_max = data.get('budget_max', 0)
    duration = data.get('duration', '').strip()
    location_str = data.get('location', 'Remote').strip()

    if not title:
        return jsonify({'error': 'Title is required'}), 400
    if not description:
        return jsonify({'error': 'Description is required'}), 400

    # Resolve category enum
    try:
        category = CategoryEnum(category_str)
    except ValueError:
        return jsonify({'error': f'Invalid category: {category_str}'}), 400

    # Resolve location enum
    location_map = {
        'Remote': LocationEnum.remote,
        'Hybrid': LocationEnum.hybrid,
        'Hybride': LocationEnum.hybrid,
        'Onsite': LocationEnum.onsite,
        'Sur site': LocationEnum.onsite,
    }
    location = location_map.get(location_str, LocationEnum.remote)

    offer = Offer(
        client_id=current_user.id,
        title=title,
        description=description,
        category=category,
        skills=skills if isinstance(skills, list) else [],
        budget_min=float(budget_min),
        budget_max=float(budget_max),
        duration=duration,
        location=location,
        proposals_count=0,
        status=OfferStatusEnum.active,
    )
    db.session.add(offer)
    db.session.commit()

    return jsonify({'offer': offer.to_dict()}), 201

@offers_bp.route('/<int:offer_id>/proposals', methods=['POST'])
@token_required
def create_proposal(current_user, offer_id):
    """Freelancer submits proposal."""
    from models import Proposal

    if current_user.role.value != 'freelancer':
        return jsonify({'error': 'Only freelancers can submit proposals'}), 403

    offer = Offer.query.get(offer_id)
    if not offer:
        return jsonify({'error': 'Offer not found'}), 404

    data = request.get_json()
    proposal = Proposal(
        offer_id=offer_id,
        freelancer_id=current_user.id,
        cover_letter=data.get('cover_letter', '').strip(),
        proposed_price=float(data.get('proposed_price', 0)),
        estimated_duration=data.get('estimated_duration', '').strip()
    )
    db.session.add(proposal)
    
    # Increment proposal count
    offer.proposals_count = (offer.proposals_count or 0) + 1
    db.session.commit()

    return jsonify({'proposal': proposal.to_dict()}), 201

@offers_bp.route('/<int:offer_id>/proposals', methods=['GET'])
@token_required
def get_offer_proposals(current_user, offer_id):
    """Client sees proposals for their offer."""
    from models import Proposal

    offer = Offer.query.get(offer_id)
    if not offer:
        return jsonify({'error': 'Offer not found'}), 404

    if offer.client_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    proposals = Proposal.query.filter_by(offer_id=offer_id).order_by(Proposal.created_at.desc()).all()
    return jsonify({'proposals': [p.to_dict() for p in proposals]}), 200
