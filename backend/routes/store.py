from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import datetime
import re
from bson import ObjectId

from app import mongo, serialize, serialize_list

store_bp = Blueprint('store', __name__, url_prefix='/api/store')

@store_bp.route('/products', methods=['GET'])
def get_products():
    """List digital products with optional filtering."""
    category = request.args.get('category', '').strip()
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    query = {}

    if category:
        query["category"] = category

    if search:
        regex = re.compile(search, re.IGNORECASE)
        query["title"] = regex

    total = mongo.db.store_products.count_documents(query)
    products = list(mongo.db.store_products.find(query)
                    .sort("created_at", -1)
                    .skip((page - 1) * limit)
                    .limit(limit))
    
    for p in products:
        seller = mongo.db.users.find_one({"_id": ObjectId(p["seller_id"])})
        p["seller_name"] = seller.get("full_name") if seller else ""
    
    return jsonify({
        "data": serialize_list(products),
        "meta": {
            "page": page,
            "total": total,
            "has_more": (page * limit) < total
        }
    }), 200


@store_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get product details."""
    product = mongo.db.store_products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return jsonify({'error': 'Product not found'}), 404
        
    seller = mongo.db.users.find_one({"_id": ObjectId(product["seller_id"])})
    product["seller_name"] = seller.get("full_name") if seller else ""

    return jsonify({'product': serialize(product)}), 200


@store_bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    """Create a new digital product (freelancers only)."""
    user_id = get_jwt_identity()
    current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    
    if current_user.get("role") != 'freelancer':
        return jsonify({'error': 'Only freelancers can create products'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required_fields = ['title', 'description', 'category', 'price']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    product_doc = {
        "seller_id": user_id,
        "title": data['title'],
        "description": data['description'],
        "category": data['category'],
        "skills": data.get('skills', []),
        "price": float(data['price']),
        "rating": 0.0,
        "sales_count": 0,
        "version": data.get('version', '1.0.0'),
        "image_url": data.get('image_url', ''),
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }

    result = mongo.db.store_products.insert_one(product_doc)
    product_doc["_id"] = result.inserted_id
    product_doc["seller_name"] = current_user.get("full_name")

    return jsonify({'product': serialize(product_doc)}), 201
