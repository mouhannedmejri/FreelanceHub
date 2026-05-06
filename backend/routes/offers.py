from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import datetime
import re
from bson import ObjectId

from app import mongo, serialize, serialize_list

offers_bp = Blueprint('offers', __name__, url_prefix='/api/offers')

@offers_bp.route('/', methods=['GET'])
def get_offers():
    """Return all active offers (freelancer/visitor view), optionally filtered by search."""
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    category_param = request.args.get('category', '').strip()
    location_param = request.args.get('location', '').strip()
    duration_param = request.args.get('duration', '').strip()
    budget_min = request.args.get('budget_min', '').strip()
    budget_max = request.args.get('budget_max', '').strip()

    query = {"status": "active"}

    if category_param:
        query["category"] = re.compile(f"^{re.escape(category_param)}$", re.IGNORECASE)

    if location_param:
        query["location"] = re.compile(f"^{re.escape(location_param)}$", re.IGNORECASE)

    if duration_param:
        query["duration"] = re.compile(re.escape(duration_param), re.IGNORECASE)

    if budget_min:
        try:
            query["budget_min"] = {"$gte": float(budget_min)}
        except ValueError:
            pass
    if budget_max:
        try:
            query["budget_max"] = {"$lte": float(budget_max)}
        except ValueError:
            pass

    if search:
        regex = re.compile(search, re.IGNORECASE)
        query["$or"] = [
            {"title": regex},
            {"description": regex},
            {"skills": {"$elemMatch": {"$regex": search, "$options": "i"}}}
        ]

    total = mongo.db.offers.count_documents(query)
    offers = list(mongo.db.offers.find(query)
                  .sort("created_at", -1)
                  .skip((page - 1) * limit)
                  .limit(limit))
    
    # populate client_name
    for o in offers:
        client = mongo.db.users.find_one({"_id": ObjectId(o["client_id"])})
        o["client_name"] = client.get("full_name") if client else ""

    return jsonify({
        "offers": serialize_list(offers),
        "total": total,
        "meta": {
            "page": page,
            "total": total,
            "has_more": (page * limit) < total
        }
    }), 200

@offers_bp.route('/mine', methods=['GET'])
@jwt_required()
def get_my_offers():
    """Return offers created by the authenticated client."""
    client_id = get_jwt_identity()
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    category_param = request.args.get('category', '').strip()
    location_param = request.args.get('location', '').strip()
    duration_param = request.args.get('duration', '').strip()
    budget_min = request.args.get('budget_min', '').strip()
    budget_max = request.args.get('budget_max', '').strip()

    query = {"client_id": client_id}

    if category_param:
        query["category"] = re.compile(f"^{re.escape(category_param)}$", re.IGNORECASE)

    if location_param:
        query["location"] = re.compile(f"^{re.escape(location_param)}$", re.IGNORECASE)

    if duration_param:
        query["duration"] = re.compile(re.escape(duration_param), re.IGNORECASE)

    if budget_min:
        try:
            query["budget_min"] = {"$gte": float(budget_min)}
        except ValueError:
            pass
    if budget_max:
        try:
            query["budget_max"] = {"$lte": float(budget_max)}
        except ValueError:
            pass

    if search:
        regex = re.compile(search, re.IGNORECASE)
        query["$or"] = [
            {"title": regex},
            {"description": regex},
            {"skills": {"$elemMatch": {"$regex": search, "$options": "i"}}}
        ]

    total = mongo.db.offers.count_documents(query)
    offers = list(mongo.db.offers.find(query)
                  .sort("created_at", -1)
                  .skip((page - 1) * limit)
                  .limit(limit))
    
    for o in offers:
        client = mongo.db.users.find_one({"_id": ObjectId(o["client_id"])})
        o["client_name"] = client.get("full_name") if client else ""

    return jsonify({
        "offers": serialize_list(offers),
        "total": total,
        "meta": {
            "page": page,
            "total": total,
            "has_more": (page * limit) < total
        }
    }), 200

@offers_bp.route('/<offer_id>', methods=['GET'])
def get_offer(offer_id):
    """Return a single offer by ID."""
    try:
        offer = mongo.db.offers.find_one({"_id": ObjectId(offer_id)})
    except Exception:
        return jsonify({'error': 'Invalid offer ID'}), 400
    if not offer:
        return jsonify({'error': 'Offer not found'}), 404
        
    client = mongo.db.users.find_one({"_id": ObjectId(offer["client_id"])})
    offer["client_name"] = client.get("full_name") if client else ""
    
    return jsonify({'offer': serialize(offer)}), 200

@offers_bp.route('/', methods=['POST'])
@jwt_required()
def create_offer():
    """Create a new offer (client only)."""
    user_id = get_jwt_identity()
    current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    
    if current_user.get("role") != 'client':
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

    if not title: return jsonify({'error': 'Title is required'}), 400
    if not description: return jsonify({'error': 'Description is required'}), 400

    offer_doc = {
        "client_id": user_id,
        "title": title,
        "description": description,
        "category": category_str,
        "skills": skills if isinstance(skills, list) else [],
        "budget_min": float(budget_min),
        "budget_max": float(budget_max),
        "duration": duration,
        "location": location_str,
        "proposals_count": 0,
        "status": "active",
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    
    result = mongo.db.offers.insert_one(offer_doc)
    offer_doc["_id"] = result.inserted_id
    offer_doc["client_name"] = current_user.get("full_name")

    return jsonify({'offer': serialize(offer_doc)}), 201

@offers_bp.route('/<offer_id>/proposals', methods=['POST'])
@jwt_required()
def create_proposal(offer_id):
    """Freelancer submits proposal."""
    user_id = get_jwt_identity()
    current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    
    if current_user.get("role") != 'freelancer':
        return jsonify({'error': 'Only freelancers can submit proposals'}), 403

    offer = mongo.db.offers.find_one({"_id": ObjectId(offer_id)})
    if not offer:
        return jsonify({'error': 'Offer not found'}), 404

    data = request.get_json()
    recommendation_context = data.get("recommendation_context") if isinstance(data, dict) else None
    proposal_doc = {
        "offer_id": offer_id,
        "freelancer_id": user_id,
        "cover_letter": data.get('cover_letter', '').strip(),
        "proposed_price": float(data.get('proposed_price', 0)),
        "estimated_duration": data.get('estimated_duration', '').strip(),
        "status": "pending",
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    if recommendation_context and isinstance(recommendation_context, dict):
        proposal_doc["recommendation_context"] = {
            "recommendation_type": recommendation_context.get("recommendation_type", ""),
            "score": recommendation_context.get("score"),
            "reason": recommendation_context.get("reason", ""),
            "tracked_at": datetime.datetime.now(datetime.timezone.utc),
        }
    
    result = mongo.db.proposals.insert_one(proposal_doc)
    proposal_doc["_id"] = result.inserted_id
    
    # Increment proposal count
    mongo.db.offers.update_one({"_id": ObjectId(offer_id)}, {"$inc": {"proposals_count": 1}})
    if proposal_doc.get("recommendation_context"):
        mongo.db.recommendation_interactions.insert_one(
            {
                "user_id": user_id,
                "item_id": offer_id,
                "item_type": "offer",
                "recommendation_type": proposal_doc["recommendation_context"].get("recommendation_type", "opportunities"),
                "action": "proposal_submitted",
                "score": proposal_doc["recommendation_context"].get("score"),
                "reason": proposal_doc["recommendation_context"].get("reason", ""),
                "created_at": datetime.datetime.now(datetime.timezone.utc),
            }
        )

    return jsonify({'proposal': serialize(proposal_doc)}), 201

@offers_bp.route('/<offer_id>/proposals', methods=['GET'])
@jwt_required()
def get_offer_proposals(offer_id):
    """Client sees proposals for their offer."""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    offer = mongo.db.offers.find_one({"_id": ObjectId(offer_id)})
    if not offer:
        return jsonify({'error': 'Offer not found'}), 404

    if offer.get("client_id") != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    query = {"offer_id": offer_id}
    total = mongo.db.proposals.count_documents(query)
    proposals = list(mongo.db.proposals.find(query)
                     .sort("created_at", -1)
                     .skip((page - 1) * limit)
                     .limit(limit))
    
    for p in proposals:
        freelancer = mongo.db.users.find_one({"_id": ObjectId(p["freelancer_id"])})
        p["freelancer"] = serialize(freelancer) if freelancer else None

    return jsonify({
        "proposals": serialize_list(proposals),
        "total": total,
        "meta": {
            "page": page,
            "total": total,
            "has_more": (page * limit) < total
        }
    }), 200


# ════════════════════════════════════════════════════════════════
# ADVANCED SEARCH & FILTERS
# ════════════════════════════════════════════════════════════════

@offers_bp.route('/search', methods=['GET'])
def search_offers():
    """Advanced search with multiple filters"""
    query = {"status": "active"}
    
    # Text search
    search = request.args.get('search', '').strip()
    if search:
        regex = re.compile(search, re.IGNORECASE)
        query["$or"] = [
            {"title": regex},
            {"description": regex},
            {"skills": {"$elemMatch": {"$regex": search, "$options": "i"}}}
        ]
    
    # Category filter
    category = request.args.get('category', '').strip()
    if category:
        query["category"] = re.compile(f"^{re.escape(category)}$", re.IGNORECASE)
    
    # Budget range
    min_budget = request.args.get('min_budget', type=float)
    max_budget = request.args.get('max_budget', type=float)
    if min_budget is not None or max_budget is not None:
        budget_query = {}
        if min_budget is not None:
            budget_query["$gte"] = min_budget
        if max_budget is not None:
            budget_query["$lte"] = max_budget
        query["budget_min"] = budget_query
    
    # Skills filter
    skills = request.args.getlist('skills')
    if skills:
        query["skills"] = {"$in": skills}
    
    # Project type filter
    project_type = request.args.get('type', '').strip()
    if project_type in ['fixed', 'hourly']:
        query["project_type"] = project_type
    
    # Experience level
    experience = request.args.get('experience', '').strip()
    if experience in ['entry', 'intermediate', 'expert']:
        query["experience_level"] = experience
    
    # Location filter
    location = request.args.get('location', '').strip()
    if location:
        query["location"] = re.compile(f"^{re.escape(location)}$", re.IGNORECASE)
    
    # Duration filter
    duration = request.args.get('duration', '').strip()
    if duration:
        query["duration"] = re.compile(re.escape(duration), re.IGNORECASE)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    total = mongo.db.offers.count_documents(query)
    offers = list(mongo.db.offers.find(query)
                  .sort("created_at", -1)
                  .skip((page - 1) * limit)
                  .limit(limit))
    
    return jsonify({
        'offers': serialize_list(offers),
        'total': total,
        'meta': {
            'page': page,
            'limit': limit,
            'total': total,
            'has_more': (page * limit) < total
        }
    }), 200


# ════════════════════════════════════════════════════════════════
# SAVED SEARCHES
# ════════════════════════════════════════════════════════════════

@offers_bp.route('/saved-searches', methods=['POST'])
@jwt_required()
def save_search():
    """Save a search with filters for later use"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Search name is required'}), 400
    
    saved_search = {
        'user_id': ObjectId(user_id),
        'name': data.get('name'),
        'filters': data.get('filters', {}),
        'alert_enabled': data.get('alert_enabled', True),
        'created_at': datetime.datetime.now(datetime.timezone.utc),
        'updated_at': datetime.datetime.now(datetime.timezone.utc)
    }
    
    result = mongo.db.saved_searches.insert_one(saved_search)
    
    return jsonify({
        'message': 'Search saved',
        'search_id': str(result.inserted_id)
    }), 201


@offers_bp.route('/saved-searches', methods=['GET'])
@jwt_required()
def get_saved_searches():
    """Get all saved searches for current user"""
    user_id = get_jwt_identity()
    
    searches = list(mongo.db.saved_searches.find(
        {'user_id': ObjectId(user_id)}
    ).sort('created_at', -1))
    
    return jsonify({'saved_searches': serialize_list(searches)}), 200


@offers_bp.route('/saved-searches/<search_id>', methods=['GET'])
@jwt_required()
def get_saved_search(search_id):
    """Get a specific saved search and execute it"""
    user_id = get_jwt_identity()
    
    search = mongo.db.saved_searches.find_one({
        '_id': ObjectId(search_id),
        'user_id': ObjectId(user_id)
    })
    
    if not search:
        return jsonify({'error': 'Saved search not found'}), 404
    
    # Execute the saved search
    query = {"status": "active"}
    filters = search.get('filters', {})
    
    # Apply filters from saved search
    if filters.get('search'):
        regex = re.compile(filters['search'], re.IGNORECASE)
        query["$or"] = [
            {"title": regex},
            {"description": regex},
            {"skills": {"$elemMatch": {"$regex": filters['search'], "$options": "i"}}}
        ]
    
    if filters.get('category'):
        query["category"] = re.compile(f"^{re.escape(filters['category'])}$", re.IGNORECASE)
    
    if filters.get('min_budget') is not None or filters.get('max_budget') is not None:
        budget_query = {}
        if filters.get('min_budget') is not None:
            budget_query["$gte"] = filters['min_budget']
        if filters.get('max_budget') is not None:
            budget_query["$lte"] = filters['max_budget']
        query["budget_min"] = budget_query
    
    if filters.get('skills'):
        query["skills"] = {"$in": filters['skills']}
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    total = mongo.db.offers.count_documents(query)
    offers = list(mongo.db.offers.find(query)
                  .sort("created_at", -1)
                  .skip((page - 1) * limit)
                  .limit(limit))
    
    return jsonify({
        'search': serialize(search),
        'offers': serialize_list(offers),
        'total': total,
        'meta': {
            'page': page,
            'limit': limit,
            'total': total,
            'has_more': (page * limit) < total
        }
    }), 200


@offers_bp.route('/saved-searches/<search_id>', methods=['DELETE'])
@jwt_required()
def delete_saved_search(search_id):
    """Delete a saved search"""
    user_id = get_jwt_identity()
    
    result = mongo.db.saved_searches.delete_one({
        '_id': ObjectId(search_id),
        'user_id': ObjectId(user_id)
    })
    
    if result.deleted_count == 0:
        return jsonify({'error': 'Saved search not found'}), 404
    
    return jsonify({'message': 'Saved search deleted'}), 200
