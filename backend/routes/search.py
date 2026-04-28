from flask import Blueprint, request, jsonify
from app import mongo, serialize, serialize_list
import re
from bson import ObjectId

search_bp = Blueprint('search', __name__, url_prefix='/api/search')

@search_bp.route('/', methods=['GET'])
def unified_search():
    """Unified search across offers, services, and users."""
    q = request.args.get('q', '').strip()
    type_filter = request.args.get('type', '').strip() # offers, services, users
    budget_min = request.args.get('budget_min', '').strip()
    budget_max = request.args.get('budget_max', '').strip()
    level = request.args.get('level', '').strip()
    remote = request.args.get('remote', '').strip()
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    results = []

    # Helper for budget query
    budget_query = {}
    if budget_min:
        try:
            budget_query["$gte"] = float(budget_min)
        except ValueError:
            pass
    if budget_max:
        try:
            budget_query["$lte"] = float(budget_max)
        except ValueError:
            pass

    # Offers
    if not type_filter or type_filter == 'offers':
        query = {"status": "active"}
        if q:
            query["$text"] = {"$search": q}
        if budget_query:
            query["budget_min"] = budget_query
        
        offers = list(mongo.db.offers.find(query).sort([("created_at", -1)]))
        for o in offers:
            o["result_type"] = "offer"
            results.append(o)

    # Services
    if not type_filter or type_filter == 'services':
        query = {}
        if q:
            query["$text"] = {"$search": q}
        if level:
            query["level"] = re.compile(f"^{re.escape(level)}$", re.IGNORECASE)
        if budget_query:
            query["price"] = budget_query
            
        services = list(mongo.db.services.find(query).sort([("created_at", -1)]))
        for s in services:
            s["result_type"] = "service"
            results.append(s)

    # Users
    if not type_filter or type_filter == 'users':
        query = {}
        if q:
            query["$or"] = [
                {"full_name": {"$regex": q, "$options": "i"}},
                {"role": {"$regex": q, "$options": "i"}}
            ]
            
        users = list(mongo.db.users.find(query).sort([("created_at", -1)]))
        for u in users:
            u.pop("password_hash", None)
            u["result_type"] = "user"
            results.append(u)

    # Note: text score sorting might be better if $text is used, 
    # but for simplicity we combined the results.
    # Pagination in memory for the mixed list
    total = len(results)
    start_idx = (page - 1) * limit
    paginated = results[start_idx:start_idx + limit]

    return jsonify({
        "data": serialize_list(paginated),
        "meta": {
            "page": page,
            "total": total,
            "has_more": (page * limit) < total
        }
    }), 200
