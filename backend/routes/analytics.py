from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime

from app import mongo, serialize

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


# ════════════════════════════════════════════════════════════════
# FREELANCER ANALYTICS
# ════════════════════════════════════════════════════════════════

@analytics_bp.route('/freelancer', methods=['GET'])
@jwt_required()
def freelancer_analytics():
    """Get comprehensive analytics for a freelancer"""
    user_id = get_jwt_identity()
    
    # Verify user is freelancer
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user.get('role') != 'freelancer':
        return jsonify({'error': 'Analytics only available for freelancers'}), 403
    
    # Profile views
    profile_views = mongo.db.profile_views.count_documents({
        'profile_id': ObjectId(user_id)
    })
    
    # Proposal stats
    proposals = list(mongo.db.proposals.find({'freelancer_id': ObjectId(user_id)}))
    proposal_stats = {
        'total': len(proposals),
        'accepted': len([p for p in proposals if p.get('status') == 'accepted']),
        'rejected': len([p for p in proposals if p.get('status') == 'rejected']),
        'pending': len([p for p in proposals if p.get('status') == 'pending']),
        'acceptance_rate': round((len([p for p in proposals if p.get('status') == 'accepted']) / len(proposals) * 100) if proposals else 0, 1)
    }
    
    # Project stats
    projects = list(mongo.db.projects.find({'freelancer_id': ObjectId(user_id)}))
    project_stats = {
        'total': len(projects),
        'active': len([p for p in projects if p.get('status') in ['in_progress', 'quoted', 'pending']]),
        'completed': len([p for p in projects if p.get('status') == 'completed']),
        'cancelled': len([p for p in projects if p.get('status') == 'cancelled'])
    }
    
    # Earnings over time (last 12 months)
    end_date = datetime.datetime.now(datetime.timezone.utc)
    start_date = end_date - datetime.timedelta(days=365)
    
    earnings_pipeline = [
        {
            '$match': {
                'freelancer_id': ObjectId(user_id),
                'status': 'completed',
                'completed_at': {'$gte': start_date}
            }
        },
        {
            '$group': {
                '_id': {
                    'year': {'$year': '$completed_at'},
                    'month': {'$month': '$completed_at'}
                },
                'total': {'$sum': '$budget_min'},
                'count': {'$sum': 1}
            }
        },
        {'$sort': {'_id.year': 1, '_id.month': 1}}
    ]
    
    earnings_by_month = list(mongo.db.projects.aggregate(earnings_pipeline))
    
    # Top skills (from accepted projects)
    skill_freq = {}
    for project in projects:
        if project.get('status') == 'completed':
            for skill in project.get('required_skills', []):
                skill_freq[skill] = skill_freq.get(skill, 0) + 1
    
    top_skills = sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Response time stats
    total_response_time = 0
    response_count = 0
    for proposal in proposals:
        if proposal.get('responded_at') and proposal.get('created_at'):
            response_time = (proposal['responded_at'] - proposal['created_at']).total_seconds() / 3600
            total_response_time += response_time
            response_count += 1
    
    avg_response_time = round(total_response_time / response_count, 1) if response_count > 0 else 0
    
    # Get profile data
    profile = mongo.db.freelancer_profiles.find_one({'user_id': ObjectId(user_id)})
    
    return jsonify({
        'profile_views': profile_views,
        'proposal_stats': proposal_stats,
        'project_stats': project_stats,
        'earnings_by_month': earnings_by_month,
        'top_skills': [{'skill': s[0], 'count': s[1]} for s in top_skills],
        'avg_response_time_hours': avg_response_time,
        'avg_rating': profile.get('avg_rating', 0) if profile else 0,
        'total_reviews': profile.get('total_reviews', 0) if profile else 0,
        'total_earned': sum(p.get('budget_min', 0) for p in projects if p.get('status') == 'completed')
    }), 200


# ════════════════════════════════════════════════════════════════
# CLIENT ANALYTICS
# ════════════════════════════════════════════════════════════════

@analytics_bp.route('/client', methods=['GET'])
@jwt_required()
def client_analytics():
    """Get comprehensive analytics for a client"""
    user_id = get_jwt_identity()
    
    # Verify user is client
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user.get('role') != 'client':
        return jsonify({'error': 'Analytics only available for clients'}), 403
    
    # Projects stats
    projects = list(mongo.db.projects.find({'client_id': ObjectId(user_id)}))
    
    project_stats = {
        'total': len(projects),
        'active': len([p for p in projects if p.get('status') in ['in_progress', 'pending', 'quoted']]),
        'completed': len([p for p in projects if p.get('status') == 'completed']),
        'cancelled': len([p for p in projects if p.get('status') == 'cancelled'])
    }
    
    # Budget analysis
    total_budget = sum(p.get('budget_min', 0) for p in projects)
    spent_budget = sum(p.get('budget_min', 0) for p in projects if p.get('status') == 'completed')
    active_budget = sum(p.get('budget_min', 0) for p in projects if p.get('status') in ['in_progress'])
    
    # Proposal stats
    offers = list(mongo.db.offers.find({'client_id': ObjectId(user_id)}))
    
    proposal_count_total = 0
    proposal_data = {}
    
    for offer in offers:
        proposals = list(mongo.db.proposals.find({'offer_id': str(offer['_id'])}))
        proposal_count_total += len(proposals)
        proposal_data[str(offer['_id'])] = len(proposals)
    
    # Top freelancers (by hire count)
    freelancer_freq = {}
    for project in projects:
        if project.get('freelancer_id'):
            freelancer_id = str(project['freelancer_id'])
            freelancer_freq[freelancer_id] = freelancer_freq.get(freelancer_id, 0) + 1
    
    top_freelancers = sorted(freelancer_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Get freelancer details
    top_freelancers_data = []
    for fid, count in top_freelancers:
        freelancer = mongo.db.users.find_one({'_id': ObjectId(fid)})
        profile = mongo.db.freelancer_profiles.find_one({'user_id': ObjectId(fid)})
        top_freelancers_data.append({
            'freelancer_id': fid,
            'name': freelancer.get('full_name', 'Unknown') if freelancer else 'Unknown',
            'hire_count': count,
            'rating': profile.get('avg_rating', 0) if profile else 0
        })
    
    # Spending over time (last 12 months)
    end_date = datetime.datetime.now(datetime.timezone.utc)
    start_date = end_date - datetime.timedelta(days=365)
    
    spending_pipeline = [
        {
            '$match': {
                'client_id': ObjectId(user_id),
                'status': 'completed',
                'completed_at': {'$gte': start_date}
            }
        },
        {
            '$group': {
                '_id': {
                    'year': {'$year': '$completed_at'},
                    'month': {'$month': '$completed_at'}
                },
                'total': {'$sum': '$budget_min'},
                'count': {'$sum': 1}
            }
        },
        {'$sort': {'_id.year': 1, '_id.month': 1}}
    ]
    
    spending_by_month = list(mongo.db.projects.aggregate(spending_pipeline))
    
    # Category breakdown
    category_freq = {}
    for offer in offers:
        cat = offer.get('category', 'Other')
        category_freq[cat] = category_freq.get(cat, 0) + 1
    
    return jsonify({
        'project_stats': project_stats,
        'budget_stats': {
            'total_budget': total_budget,
            'spent_budget': spent_budget,
            'active_budget': active_budget,
            'remaining_budget': total_budget - spent_budget
        },
        'proposal_count': proposal_count_total,
        'top_freelancers': top_freelancers_data,
        'spending_by_month': spending_by_month,
        'category_breakdown': [{'category': k, 'count': v} for k, v in category_freq.items()],
        'avg_projects_completion_time': 0  # TODO: Calculate
    }), 200


# ════════════════════════════════════════════════════════════════
# GENERAL ANALYTICS
# ════════════════════════════════════════════════════════════════

@analytics_bp.route('/personal', methods=['GET'])
@jwt_required()
def personal_analytics():
    """Get personal activity analytics"""
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get user role
    role = user.get('role', 'client')
    
    if role == 'freelancer':
        return freelancer_analytics()
    elif role == 'client':
        return client_analytics()
    else:
        return jsonify({'error': 'Analytics not available for this role'}), 403


@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard_analytics():
    """Get dashboard summary for quick view"""
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    role = user.get('role', 'client')
    
    if role == 'freelancer':
        # Freelancer dashboard
        proposals = mongo.db.proposals.count_documents({'freelancer_id': ObjectId(user_id)})
        projects = mongo.db.projects.count_documents({'freelancer_id': ObjectId(user_id), 'status': 'in_progress'})
        profile = mongo.db.freelancer_profiles.find_one({'user_id': ObjectId(user_id)})
        
        return jsonify({
            'role': 'freelancer',
            'active_projects': projects,
            'pending_proposals': proposals,
            'profile_completion': profile.get('completion_percentage', 0) if profile else 0,
            'avg_rating': profile.get('avg_rating', 0) if profile else 0
        }), 200
    
    elif role == 'client':
        # Client dashboard
        active_projects = mongo.db.projects.count_documents({
            'client_id': ObjectId(user_id),
            'status': 'in_progress'
        })
        active_offers = mongo.db.offers.count_documents({
            'client_id': ObjectId(user_id),
            'status': 'active'
        })
        pending_proposals = mongo.db.proposals.count_documents({
            'status': 'pending'
        })
        
        return jsonify({
            'role': 'client',
            'active_projects': active_projects,
            'active_offers': active_offers,
            'pending_proposals': pending_proposals
        }), 200
    
    else:
        return jsonify({'error': 'Analytics not available for this role'}), 403
