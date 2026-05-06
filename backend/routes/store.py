from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import datetime
import re
import uuid
import hashlib
import os
from bson import ObjectId
from werkzeug.utils import secure_filename

from app import mongo, serialize, serialize_list

store_bp = Blueprint('store', __name__, url_prefix='/api/store')

ALLOWED_EXTENSIONS = {'zip', 'pdf', 'fig', 'sketch', 'psd', 'ai', 'png', 'jpg', 'jpeg', 'svg', 'doc', 'docx', 'xls', 'xlsx', 'pptx'}
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'store_products')
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAIN_CATEGORIES = [
    'website_templates', 'mobile_app_templates', 'design_assets',
    'code_scripts', 'business_documents'
]
LICENSE_TYPES = ['single', 'multiple', 'unlimited']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_download_token():
    return uuid.uuid4().hex + uuid.uuid4().hex

def generate_checksum(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

# ─── PUBLIC: Browse Products ────────────────────────────────────────

@store_bp.route('/products', methods=['GET'])
def get_products():
    """List digital products with enhanced filtering."""
    category = request.args.get('category', '').strip()
    main_category = request.args.get('main_category', '').strip()
    search = request.args.get('search', '').strip()
    file_type = request.args.get('file_type', '').strip()
    license_type = request.args.get('license_type', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    is_free = request.args.get('is_free', '').strip()
    is_featured = request.args.get('is_featured', '').strip()
    sort_by = request.args.get('sort_by', 'recent').strip()
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    tag = request.args.get('tag', '').strip()

    query = {"is_deleted": {"$ne": True}}

    if category:
        query["category"] = category
    if main_category:
        query["main_category"] = main_category
    if search:
        regex = re.compile(search, re.IGNORECASE)
        query["$or"] = [{"title": regex}, {"description": regex}, {"tags": regex}]
    if file_type:
        query["file_type"] = file_type
    if license_type:
        query["license_type"] = license_type
    if tag:
        query["tags"] = tag
    if is_free == 'true':
        query["price"] = 0
    elif is_free == 'false':
        query["price"] = {"$gt": 0}
    if min_price is not None:
        query.setdefault("price", {})
        if isinstance(query["price"], dict):
            query["price"]["$gte"] = min_price
        else:
            query["price"] = {"$gte": min_price}
    if max_price is not None:
        query.setdefault("price", {})
        if isinstance(query["price"], dict):
            query["price"]["$lte"] = max_price
        else:
            query["price"] = {"$lte": max_price}
    if is_featured == 'true':
        query["is_featured"] = True

    sort_map = {
        'recent': ("created_at", -1),
        'popular': ("download_count", -1),
        'price_low': ("price", 1),
        'price_high': ("price", -1),
        'rating': ("rating", -1),
    }
    sort_field, sort_dir = sort_map.get(sort_by, ("created_at", -1))

    total = mongo.db.store_products.count_documents(query)
    products = list(mongo.db.store_products.find(query)
                    .sort(sort_field, sort_dir)
                    .skip((page - 1) * limit)
                    .limit(limit))

    for p in products:
        seller = mongo.db.users.find_one({"_id": ObjectId(p["seller_id"])})
        p["seller_name"] = seller.get("full_name") if seller else ""
        p["seller_avatar"] = seller.get("avatar_url", "") if seller else ""

    return jsonify({
        "data": serialize_list(products),
        "meta": {"page": page, "total": total, "has_more": (page * limit) < total}
    }), 200


@store_bp.route('/products/featured', methods=['GET'])
def get_featured_products():
    """Get featured products for carousel."""
    products = list(mongo.db.store_products.find(
        {"is_featured": True, "is_deleted": {"$ne": True}}
    ).sort("download_count", -1).limit(10))
    for p in products:
        seller = mongo.db.users.find_one({"_id": ObjectId(p["seller_id"])})
        p["seller_name"] = seller.get("full_name") if seller else ""
    return jsonify({"data": serialize_list(products)}), 200


@store_bp.route('/products/categories', methods=['GET'])
def get_categories():
    """Get all available categories with counts."""
    pipeline = [
        {"$match": {"is_deleted": {"$ne": True}}},
        {"$group": {"_id": "$main_category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    results = list(mongo.db.store_products.aggregate(pipeline))
    categories = [{"id": r["_id"], "count": r["count"]} for r in results if r["_id"]]
    return jsonify({"categories": categories}), 200


@store_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get product details with seller info and reviews."""
    product = mongo.db.store_products.find_one({"_id": ObjectId(product_id), "is_deleted": {"$ne": True}})
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Increment view count
    mongo.db.store_products.update_one({"_id": ObjectId(product_id)}, {"$inc": {"view_count": 1}})

    seller = mongo.db.users.find_one({"_id": ObjectId(product["seller_id"])})
    product["seller_name"] = seller.get("full_name") if seller else ""
    product["seller_avatar"] = seller.get("avatar_url", "") if seller else ""

    # Seller stats
    seller_products_count = mongo.db.store_products.count_documents({"seller_id": product["seller_id"], "is_deleted": {"$ne": True}})
    product["seller_products_count"] = seller_products_count

    profile = mongo.db.freelancer_profiles.find_one({"user_id": product["seller_id"]})
    product["seller_rating"] = profile.get("avg_rating", 0) if profile else 0

    # Reviews
    reviews = list(mongo.db.product_reviews.find({"product_id": product_id}).sort("created_at", -1).limit(10))
    for r in reviews:
        reviewer = mongo.db.users.find_one({"_id": ObjectId(r["user_id"])})
        r["reviewer_name"] = reviewer.get("full_name", "") if reviewer else ""
    product["reviews"] = serialize_list(reviews)

    # Related products
    related = list(mongo.db.store_products.find({
        "main_category": product.get("main_category"),
        "_id": {"$ne": ObjectId(product_id)},
        "is_deleted": {"$ne": True}
    }).limit(4))
    for rp in related:
        s = mongo.db.users.find_one({"_id": ObjectId(rp["seller_id"])})
        rp["seller_name"] = s.get("full_name") if s else ""
    product["related_products"] = serialize_list(related)

    return jsonify({'product': serialize(product)}), 200


# ─── SELLER: Product Management ────────────────────────────────────

@store_bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    """Create a new digital product with file upload."""
    user_id = get_jwt_identity()
    current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if current_user.get("role") != 'freelancer':
        return jsonify({'error': 'Only freelancers can create products'}), 403

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', '').strip()
    price = request.form.get('price', '0')

    if not title or not description or not category:
        return jsonify({'error': 'Missing required fields: title, description, category'}), 400

    # Handle product file
    product_file = request.files.get('product_file')
    file_path = ""
    file_size = "0"
    file_checksum = ""
    if product_file and allowed_file(product_file.filename):
        filename = secure_filename(f"{uuid.uuid4().hex}_{product_file.filename}")
        filepath = os.path.join(UPLOAD_DIR, filename)
        product_file.save(filepath)
        file_path = filepath
        file_size = str(os.path.getsize(filepath))
        file_checksum = generate_checksum(filepath)

    # Handle preview images
    preview_images = []
    for key in request.files:
        if key.startswith('preview_image'):
            img = request.files[key]
            if img:
                img_name = secure_filename(f"{uuid.uuid4().hex}_{img.filename}")
                img_path = os.path.join(UPLOAD_DIR, img_name)
                img.save(img_path)
                preview_images.append(f"/api/store/files/{img_name}")

    # Parse arrays from form
    def parse_list(key):
        val = request.form.get(key, '')
        return [x.strip() for x in val.split(',') if x.strip()] if val else []

    now = datetime.datetime.now(datetime.timezone.utc)
    product_doc = {
        "seller_id": user_id,
        "title": title,
        "description": description,
        "category": category,
        "main_category": request.form.get('main_category', ''),
        "sub_category": request.form.get('sub_category', ''),
        "tags": parse_list('tags'),
        "file_type": request.form.get('file_type', ''),
        "skills": parse_list('skills'),
        "price": float(price),
        "sale_price": float(request.form.get('sale_price', '0')) or None,
        "rating": 0.0,
        "sales_count": 0,
        "download_count": 0,
        "view_count": 0,
        "version": request.form.get('version', '1.0.0'),
        "image_url": preview_images[0] if preview_images else request.form.get('image_url', ''),
        "preview_images": preview_images,
        "demo_url": request.form.get('demo_url', ''),
        "file_size": file_size,
        "file_path": file_path,
        "file_checksum": file_checksum,
        "compatibility": parse_list('compatibility'),
        "whats_included": parse_list('whats_included'),
        "license_type": request.form.get('license_type', 'single'),
        "is_featured": False,
        "support_included": request.form.get('support_included', 'false') == 'true',
        "is_deleted": False,
        "last_updated": now,
        "created_at": now
    }

    result = mongo.db.store_products.insert_one(product_doc)
    product_doc["_id"] = result.inserted_id
    product_doc["seller_name"] = current_user.get("full_name")

    return jsonify({'product': serialize(product_doc)}), 201


@store_bp.route('/products/<product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """Update an existing product."""
    user_id = get_jwt_identity()
    product = mongo.db.store_products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    if product["seller_id"] != user_id:
        return jsonify({'error': 'Not authorized'}), 403

    data = request.get_json() or {}
    allowed_fields = [
        'title', 'description', 'category', 'main_category', 'sub_category',
        'tags', 'file_type', 'skills', 'price', 'sale_price', 'version',
        'demo_url', 'compatibility', 'whats_included', 'license_type',
        'support_included', 'image_url', 'preview_images'
    ]
    update = {}
    for f in allowed_fields:
        if f in data:
            update[f] = data[f]
    update["last_updated"] = datetime.datetime.now(datetime.timezone.utc)

    mongo.db.store_products.update_one({"_id": ObjectId(product_id)}, {"$set": update})
    updated = mongo.db.store_products.find_one({"_id": ObjectId(product_id)})
    return jsonify({'product': serialize(updated)}), 200


@store_bp.route('/products/<product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """Soft delete a product."""
    user_id = get_jwt_identity()
    product = mongo.db.store_products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    if product["seller_id"] != user_id:
        return jsonify({'error': 'Not authorized'}), 403

    mongo.db.store_products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"is_deleted": True, "deleted_at": datetime.datetime.now(datetime.timezone.utc)}}
    )
    return jsonify({'message': 'Product deleted'}), 200


# ─── SELLER: Dashboard & Analytics ─────────────────────────────────

@store_bp.route('/seller/products', methods=['GET'])
@jwt_required()
def get_seller_products():
    """Get seller's own products."""
    user_id = get_jwt_identity()
    products = list(mongo.db.store_products.find(
        {"seller_id": user_id, "is_deleted": {"$ne": True}}
    ).sort("created_at", -1))
    return jsonify({"data": serialize_list(products)}), 200


@store_bp.route('/seller/analytics', methods=['GET'])
@jwt_required()
def get_seller_analytics():
    """Get seller sales stats and analytics."""
    user_id = get_jwt_identity()
    now = datetime.datetime.now(datetime.timezone.utc)

    products = list(mongo.db.store_products.find(
        {"seller_id": user_id, "is_deleted": {"$ne": True}}
    ))
    product_ids = [str(p["_id"]) for p in products]

    total_products = len(products)
    total_views = sum(p.get("view_count", 0) for p in products)
    total_downloads = sum(p.get("download_count", 0) for p in products)
    total_sales = sum(p.get("sales_count", 0) for p in products)

    # Revenue from purchases
    purchases = list(mongo.db.store_purchases.find({"product_id": {"$in": product_ids}}))
    total_revenue = sum(p.get("amount", 0) for p in purchases)

    # Monthly revenue (last 6 months)
    monthly_revenue = []
    for i in range(5, -1, -1):
        month_start = now.replace(day=1) - datetime.timedelta(days=30 * i)
        month_end = month_start + datetime.timedelta(days=30)
        month_purchases = [
            p for p in purchases
            if month_start <= p.get("purchase_date", now) < month_end
        ]
        monthly_revenue.append({
            "month": month_start.strftime("%b %Y"),
            "revenue": sum(p.get("amount", 0) for p in month_purchases),
            "sales": len(month_purchases)
        })

    # Top products
    top_products = sorted(products, key=lambda x: x.get("sales_count", 0), reverse=True)[:5]

    # Recent sales
    recent_sales = list(mongo.db.store_purchases.find(
        {"product_id": {"$in": product_ids}}
    ).sort("purchase_date", -1).limit(10))
    for s in recent_sales:
        buyer = mongo.db.users.find_one({"_id": ObjectId(s["buyer_id"])})
        s["buyer_name"] = buyer.get("full_name", "") if buyer else ""
        prod = mongo.db.store_products.find_one({"_id": ObjectId(s["product_id"])})
        s["product_title"] = prod.get("title", "") if prod else ""

    return jsonify({
        "total_products": total_products,
        "total_views": total_views,
        "total_downloads": total_downloads,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "monthly_revenue": monthly_revenue,
        "top_products": serialize_list(top_products[:5]),
        "recent_sales": serialize_list(recent_sales)
    }), 200


# ─── PURCHASES ──────────────────────────────────────────────────────

@store_bp.route('/products/<product_id>/purchase', methods=['POST'])
@jwt_required()
def purchase_product(product_id):
    """Create a purchase record for a product."""
    user_id = get_jwt_identity()
    product = mongo.db.store_products.find_one({"_id": ObjectId(product_id), "is_deleted": {"$ne": True}})
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Check if already purchased
    existing = mongo.db.store_purchases.find_one({
        "buyer_id": user_id, "product_id": product_id, "status": "completed"
    })
    if existing:
        return jsonify({'error': 'Already purchased', 'purchase': serialize(existing)}), 409

    now = datetime.datetime.now(datetime.timezone.utc)
    price = product.get("sale_price") or product.get("price", 0)
    download_token = generate_download_token()

    purchase_doc = {
        "buyer_id": user_id,
        "product_id": product_id,
        "seller_id": product["seller_id"],
        "amount": price,
        "currency": "EUR",
        "payment_method": "stripe_placeholder",
        "payment_intent_id": f"pi_{uuid.uuid4().hex[:24]}",
        "status": "completed",
        "download_token": download_token,
        "download_count": 0,
        "download_limit": 5,
        "download_history": [],
        "purchase_date": now,
        "refund_eligible": True,
        "refund_deadline": now + datetime.timedelta(days=14),
    }

    result = mongo.db.store_purchases.insert_one(purchase_doc)
    purchase_doc["_id"] = result.inserted_id

    # Update product stats
    mongo.db.store_products.update_one(
        {"_id": ObjectId(product_id)},
        {"$inc": {"sales_count": 1, "download_count": 1}}
    )

    # Create notification for seller
    mongo.db.notifications.insert_one({
        "user_id": product["seller_id"],
        "type": "sale",
        "title": "Nouvelle vente !",
        "body": f"Votre produit '{product['title']}' a été acheté.",
        "is_read": False,
        "created_at": now
    })

    return jsonify({'purchase': serialize(purchase_doc), 'download_token': download_token}), 201


@store_bp.route('/purchases', methods=['GET'])
@jwt_required()
def get_purchases():
    """Get user's purchased products."""
    user_id = get_jwt_identity()
    purchases = list(mongo.db.store_purchases.find(
        {"buyer_id": user_id}
    ).sort("purchase_date", -1))

    for p in purchases:
        product = mongo.db.store_products.find_one({"_id": ObjectId(p["product_id"])})
        if product:
            p["product"] = serialize(product)
            seller = mongo.db.users.find_one({"_id": ObjectId(product["seller_id"])})
            p["seller_name"] = seller.get("full_name", "") if seller else ""

    return jsonify({"data": serialize_list(purchases)}), 200


@store_bp.route('/purchases/<purchase_id>/download', methods=['GET'])
@jwt_required()
def download_purchase(purchase_id):
    """Generate download for a purchased product."""
    user_id = get_jwt_identity()
    purchase = mongo.db.store_purchases.find_one({"_id": ObjectId(purchase_id)})
    if not purchase:
        return jsonify({'error': 'Purchase not found'}), 404
    if purchase["buyer_id"] != user_id:
        return jsonify({'error': 'Not authorized'}), 403
    if purchase.get("download_count", 0) >= purchase.get("download_limit", 5):
        return jsonify({'error': 'Download limit reached'}), 403

    product = mongo.db.store_products.find_one({"_id": ObjectId(purchase["product_id"])})
    if not product or not product.get("file_path"):
        return jsonify({'error': 'File not available'}), 404

    now = datetime.datetime.now(datetime.timezone.utc)
    ip_address = request.remote_addr

    # Update download count and history
    mongo.db.store_purchases.update_one(
        {"_id": ObjectId(purchase_id)},
        {
            "$inc": {"download_count": 1},
            "$push": {"download_history": {"date": now, "ip": ip_address}}
        }
    )

    if os.path.exists(product["file_path"]):
        return send_file(product["file_path"], as_attachment=True)
    else:
        # Return a download URL placeholder
        token = purchase.get("download_token", "")
        return jsonify({
            "download_url": f"/api/store/files/download/{token}",
            "remaining_downloads": purchase.get("download_limit", 5) - purchase.get("download_count", 0) - 1
        }), 200


# ─── REVIEWS ────────────────────────────────────────────────────────

@store_bp.route('/products/<product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    """Get reviews for a product."""
    reviews = list(mongo.db.product_reviews.find(
        {"product_id": product_id}
    ).sort("created_at", -1))
    for r in reviews:
        user = mongo.db.users.find_one({"_id": ObjectId(r["user_id"])})
        r["reviewer_name"] = user.get("full_name", "") if user else ""
    return jsonify({"data": serialize_list(reviews)}), 200


@store_bp.route('/products/<product_id>/reviews', methods=['POST'])
@jwt_required()
def create_review(product_id):
    """Leave a review for a purchased product."""
    user_id = get_jwt_identity()

    # Verify purchase
    purchase = mongo.db.store_purchases.find_one({
        "buyer_id": user_id, "product_id": product_id, "status": "completed"
    })
    if not purchase:
        return jsonify({'error': 'You must purchase this product before reviewing'}), 403

    # Check existing review
    existing = mongo.db.product_reviews.find_one({"user_id": user_id, "product_id": product_id})
    if existing:
        return jsonify({'error': 'You already reviewed this product'}), 409

    data = request.get_json()
    if not data or 'rating' not in data:
        return jsonify({'error': 'Rating is required'}), 400

    now = datetime.datetime.now(datetime.timezone.utc)
    review_doc = {
        "user_id": user_id,
        "product_id": product_id,
        "rating": min(5, max(1, int(data["rating"]))),
        "comment": data.get("comment", ""),
        "created_at": now
    }
    mongo.db.product_reviews.insert_one(review_doc)

    # Update product average rating
    all_reviews = list(mongo.db.product_reviews.find({"product_id": product_id}))
    avg = sum(r["rating"] for r in all_reviews) / len(all_reviews)
    mongo.db.store_products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"rating": round(avg, 1), "review_count": len(all_reviews)}}
    )

    return jsonify({'review': serialize(review_doc)}), 201


# ─── REFUNDS ────────────────────────────────────────────────────────

@store_bp.route('/purchases/<purchase_id>/refund', methods=['POST'])
@jwt_required()
def request_refund(purchase_id):
    """Request a refund for a purchase."""
    user_id = get_jwt_identity()
    purchase = mongo.db.store_purchases.find_one({"_id": ObjectId(purchase_id)})
    if not purchase:
        return jsonify({'error': 'Purchase not found'}), 404
    if purchase["buyer_id"] != user_id:
        return jsonify({'error': 'Not authorized'}), 403

    now = datetime.datetime.now(datetime.timezone.utc)
    if now > purchase.get("refund_deadline", now):
        return jsonify({'error': 'Refund period has expired'}), 400

    data = request.get_json() or {}
    mongo.db.store_purchases.update_one(
        {"_id": ObjectId(purchase_id)},
        {"$set": {
            "status": "refund_requested",
            "refund_reason": data.get("reason", ""),
            "refund_requested_at": now
        }}
    )
    return jsonify({'message': 'Refund requested successfully'}), 200


# ─── FILE SERVING ───────────────────────────────────────────────────

@store_bp.route('/files/<filename>', methods=['GET'])
def serve_file(filename):
    """Serve uploaded store files (preview images)."""
    filepath = os.path.join(UPLOAD_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify({'error': 'File not found'}), 404
