from flask import Blueprint, request, jsonify
from models import db, Product, ProductCategoryEnum, User
from routes.auth import token_required

store_bp = Blueprint('store', __name__, url_prefix='/api/store')

@store_bp.route('/products', methods=['GET'])
def get_products():
    """List digital products with optional filtering."""
    category = request.args.get('category', '').strip()
    search = request.args.get('search', '').strip()

    query = Product.query

    if category:
        try:
            # Map frontend category names or enum values
            cat_enum = ProductCategoryEnum(category)
            query = query.filter(Product.category == cat_enum)
        except ValueError:
            pass # Ignore invalid category filter

    if search:
        query = query.filter(Product.title.ilike(f'%{search}%'))

    products = query.order_by(Product.created_at.desc()).all()
    
    return jsonify({'products': [p.to_dict() for p in products]}), 200


@store_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get product details."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify({'product': product.to_dict()}), 200


@store_bp.route('/products', methods=['POST'])
@token_required
def create_product(current_user):
    """Create a new digital product (freelancers only)."""
    if current_user.role.value != 'freelancer':
        return jsonify({'error': 'Only freelancers can create products'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required_fields = ['title', 'description', 'category', 'price']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        cat_enum = ProductCategoryEnum(data['category'])
    except ValueError:
        return jsonify({'error': 'Invalid category'}), 400

    product = Product(
        seller_id=current_user.id,
        title=data['title'],
        description=data['description'],
        category=cat_enum,
        skills=data.get('skills', []),
        price=float(data['price']),
        version=data.get('version', '1.0.0'),
        image_url=data.get('image_url', '')
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({'product': product.to_dict()}), 201
