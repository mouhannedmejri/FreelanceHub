from flask import Blueprint, jsonify

home_bp = Blueprint('home', __name__, url_prefix='/api/home')


@home_bp.route('/stats', methods=['GET'])
def get_stats():
    """Return platform-wide stats for the home hero section."""
    return jsonify({
        'freelancers': 15000,
        'projects': 50000,
        'clients': 12000,
    }), 200
