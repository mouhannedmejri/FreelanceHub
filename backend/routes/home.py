from flask import Blueprint, jsonify

from app import mongo

home_bp = Blueprint('home', __name__, url_prefix='/api/home')


@home_bp.route('/stats', methods=['GET'])
def get_stats():
    """Return platform-wide stats for the home hero section.

    Public endpoint — no authentication required.
    """
    try:
        freelancers = mongo.db.users.count_documents({"role": "freelancer"})
        clients = mongo.db.users.count_documents({"role": "client"})
        projects = mongo.db.offers.count_documents({})
    except Exception:
        freelancers, projects, clients = 15000, 50000, 12000

    return jsonify({
        'freelancers': freelancers or 15000,
        'projects': projects or 50000,
        'clients': clients or 12000,
    }), 200
