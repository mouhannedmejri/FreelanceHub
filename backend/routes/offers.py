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
        "data": serialize_list(offers),
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
        "data": serialize_list(offers),
        "meta": {
            "page": page,
            "total": total,
            "has_more": (page * limit) < total
        }
    }), 200

@offers_bp.route('/<offer_id>', methods=['GET'])
def get_offer(offer_id):
    """Return a single offer by ID."""
    offer = mongo.db.offers.find_one({"_id": ObjectId(offer_id)})
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
    proposal_doc = {
        "offer_id": offer_id,
        "freelancer_id": user_id,
        "cover_letter": data.get('cover_letter', '').strip(),
        "proposed_price": float(data.get('proposed_price', 0)),
        "estimated_duration": data.get('estimated_duration', '').strip(),
        "status": "pending",
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    
    result = mongo.db.proposals.insert_one(proposal_doc)
    proposal_doc["_id"] = result.inserted_id
    
    # Increment proposal count
    mongo.db.offers.update_one({"_id": ObjectId(offer_id)}, {"$inc": {"proposals_count": 1}})

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
        "data": serialize_list(proposals),
        "meta": {
            "page": page,
            "total": total,
            "has_more": (page * limit) < total
        }
    }), 200
