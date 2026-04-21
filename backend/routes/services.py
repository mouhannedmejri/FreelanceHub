from flask import Blueprint, request, jsonify
from models import db, Service, CategoryEnum

services_bp = Blueprint('services', __name__, url_prefix='/api/services')


@services_bp.route('/', methods=['GET'])
def get_services():
    """Return a paginated, filterable list of services."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    category = request.args.get('category', '').strip()
    search = request.args.get('search', '').strip()

    query = Service.query

    # Filter by category
    if category:
        try:
            cat_enum = CategoryEnum(category)
            query = query.filter_by(category=cat_enum)
        except ValueError:
            pass  # ignore invalid category, return all

    # Search in title and description
    if search:
        like_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Service.title.ilike(like_term),
                Service.description.ilike(like_term),
            )
        )

    total = query.count()
    services = (
        query.order_by(Service.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return jsonify({
        'services': [s.to_dict() for s in services],
        'total': total,
        'page': page,
        'per_page': per_page,
        'has_more': (page * per_page) < total,
    }), 200


@services_bp.route('/<int:service_id>', methods=['GET'])
def get_service(service_id):
    """Return a single service by ID."""
    service = Service.query.get(service_id)
    if not service:
        return jsonify({'error': 'Service not found'}), 404
    return jsonify({'service': service.to_dict()}), 200
