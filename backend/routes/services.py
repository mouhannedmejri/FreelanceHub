from flask import Blueprint, request, jsonify
from bson import ObjectId
import re
from app import mongo, serialize, serialize_list

services_bp = Blueprint('services', __name__, url_prefix='/api/services')

@services_bp.route('/', methods=['GET'])
def get_services():
    """Return a paginated, filterable list of services."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    category = request.args.get('category', '').strip()
    search = request.args.get('search', '').strip()
    level = request.args.get('level', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()

    query = {}

    if category:
        query["category"] = re.compile(f"^{re.escape(category)}$", re.IGNORECASE)

    if level:
        query["level"] = re.compile(f"^{re.escape(level)}$", re.IGNORECASE)

    if min_price or max_price:
        query["price_from"] = {}
        if min_price:
            try:
                query["price_from"]["$gte"] = float(min_price)
            except ValueError:
                pass
        if max_price:
            try:
                query["price_from"]["$lte"] = float(max_price)
            except ValueError:
                pass
        if not query["price_from"]:
            del query["price_from"]

    if search:
        regex = re.compile(search, re.IGNORECASE)
        query["$or"] = [
            {"title": regex},
            {"description": regex},
            {"skills": {"$elemMatch": {"$regex": search, "$options": "i"}}}
        ]

    total = mongo.db.services.count_documents(query)
    services = list(mongo.db.services.find(query)
                    .sort("created_at", -1)
                    .skip((page - 1) * per_page)
                    .limit(per_page))

    for s in services:
        freelancer = mongo.db.users.find_one({"_id": ObjectId(s["freelancer_id"])})
        if freelancer:
            name = freelancer.get("full_name", "")
            parts = [p[0].upper() for p in name.split() if p]
            initials = "".join(parts)[:2]
            s["freelancer"] = {
                "id": str(freelancer["_id"]),
                "name": name,
                "avatar_initials": initials
            }
        else:
            s["freelancer"] = None

    return jsonify({
        'services': serialize_list(services),
        'total': total,
        'page': page,
        'per_page': per_page,
        'has_more': (page * per_page) < total,
    }), 200

@services_bp.route('/<service_id>', methods=['GET'])
def get_service(service_id):
    """Return a single service by ID."""
    service = mongo.db.services.find_one({"_id": ObjectId(service_id)})
    if not service:
        return jsonify({'error': 'Service not found'}), 404
        
    freelancer = mongo.db.users.find_one({"_id": ObjectId(service["freelancer_id"])})
    if freelancer:
        name = freelancer.get("full_name", "")
        parts = [p[0].upper() for p in name.split() if p]
        initials = "".join(parts)[:2]
        service["freelancer"] = {
            "id": str(freelancer["_id"]),
            "name": name,
            "avatar_initials": initials
        }
    else:
        service["freelancer"] = None
    
    return jsonify({'service': serialize(service)}), 200
