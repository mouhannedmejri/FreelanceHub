from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime

from app import mongo, serialize, serialize_list

support_bp = Blueprint('support', __name__, url_prefix='/api/support')


# ════════════════════════════════════════════════════════════════
# SUPPORT TICKETS
# ════════════════════════════════════════════════════════════════

@support_bp.route('/tickets', methods=['POST'])
@jwt_required()
def create_ticket():
    """Create a new support ticket"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('subject') or not data.get('description'):
        return jsonify({'error': 'Subject and description are required'}), 400
    
    ticket = {
        'user_id': ObjectId(user_id),
        'subject': data.get('subject'),
        'description': data.get('description'),
        'category': data.get('category', 'general'),
        'priority': data.get('priority', 'normal'),
        'status': 'open',
        'attachments': [],
        'messages': [{
            'author_id': ObjectId(user_id),
            'message': data.get('description'),
            'timestamp': datetime.datetime.now(datetime.timezone.utc)
        }],
        'created_at': datetime.datetime.now(datetime.timezone.utc),
        'updated_at': datetime.datetime.now(datetime.timezone.utc),
        'assigned_to': None
    }
    
    result = mongo.db.support_tickets.insert_one(ticket)
    ticket['_id'] = result.inserted_id
    
    # Notify support team (implement email notification)
    # TODO: send_email to support team
    
    return jsonify({
        'message': 'Ticket created',
        'ticket': serialize(ticket)
    }), 201


@support_bp.route('/tickets/<ticket_id>', methods=['GET'])
@jwt_required()
def get_ticket(ticket_id):
    """Get a specific support ticket"""
    user_id = get_jwt_identity()
    
    try:
        ticket = mongo.db.support_tickets.find_one({'_id': ObjectId(ticket_id)})
    except:
        return jsonify({'error': 'Invalid ticket ID'}), 400
    
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    # User can only view their own tickets or support staff can view any
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if str(ticket['user_id']) != user_id and user.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({'ticket': serialize(ticket)}), 200


@support_bp.route('/tickets', methods=['GET'])
@jwt_required()
def get_my_tickets():
    """Get all support tickets for current user"""
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    # Admin can see all tickets
    if user.get('role') == 'admin':
        query = {}
    else:
        query = {'user_id': ObjectId(user_id)}
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    status_filter = request.args.get('status')
    
    if status_filter:
        query['status'] = status_filter
    
    total = mongo.db.support_tickets.count_documents(query)
    tickets = list(mongo.db.support_tickets.find(query)
                   .sort('updated_at', -1)
                   .skip((page - 1) * limit)
                   .limit(limit))
    
    return jsonify({
        'tickets': serialize_list(tickets),
        'total': total,
        'meta': {
            'page': page,
            'limit': limit,
            'total': total,
            'has_more': (page * limit) < total
        }
    }), 200


@support_bp.route('/tickets/<ticket_id>/reply', methods=['POST'])
@jwt_required()
def reply_to_ticket(ticket_id):
    """Add a reply to a support ticket"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('message'):
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        ticket = mongo.db.support_tickets.find_one({'_id': ObjectId(ticket_id)})
    except:
        return jsonify({'error': 'Invalid ticket ID'}), 400
    
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if str(ticket['user_id']) != user_id and user.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    reply = {
        'author_id': ObjectId(user_id),
        'message': data.get('message'),
        'timestamp': datetime.datetime.now(datetime.timezone.utc),
        'is_internal': data.get('is_internal', False)
    }
    
    mongo.db.support_tickets.update_one(
        {'_id': ObjectId(ticket_id)},
        {
            '$push': {'messages': reply},
            '$set': {'updated_at': datetime.datetime.now(datetime.timezone.utc)}
        }
    )
    
    return jsonify({'message': 'Reply added'}), 200


@support_bp.route('/tickets/<ticket_id>/status', methods=['PUT'])
@jwt_required()
def update_ticket_status(ticket_id):
    """Update ticket status (admin only)"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user.get('role') != 'admin':
        return jsonify({'error': 'Only admins can update ticket status'}), 403
    
    valid_statuses = ['open', 'in_progress', 'resolved', 'closed']
    status = data.get('status')
    
    if status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
    
    try:
        mongo.db.support_tickets.update_one(
            {'_id': ObjectId(ticket_id)},
            {
                '$set': {
                    'status': status,
                    'updated_at': datetime.datetime.now(datetime.timezone.utc)
                }
            }
        )
    except:
        return jsonify({'error': 'Failed to update ticket'}), 400
    
    return jsonify({'message': 'Ticket status updated'}), 200


@support_bp.route('/tickets/<ticket_id>/assign', methods=['PUT'])
@jwt_required()
def assign_ticket(ticket_id):
    """Assign ticket to support staff (admin only)"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user.get('role') != 'admin':
        return jsonify({'error': 'Only admins can assign tickets'}), 403
    
    assigned_to = data.get('assigned_to')
    
    if assigned_to:
        # Verify assigned user exists
        assigned_user = mongo.db.users.find_one({'_id': ObjectId(assigned_to)})
        if not assigned_user:
            return jsonify({'error': 'User not found'}), 404
    
    mongo.db.support_tickets.update_one(
        {'_id': ObjectId(ticket_id)},
        {
            '$set': {
                'assigned_to': ObjectId(assigned_to) if assigned_to else None,
                'updated_at': datetime.datetime.now(datetime.timezone.utc)
            }
        }
    )
    
    return jsonify({'message': 'Ticket assigned'}), 200


@support_bp.route('/tickets/<ticket_id>/priority', methods=['PUT'])
@jwt_required()
def update_ticket_priority(ticket_id):
    """Update ticket priority (admin only)"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user.get('role') != 'admin':
        return jsonify({'error': 'Only admins can update priority'}), 403
    
    valid_priorities = ['low', 'normal', 'high', 'urgent']
    priority = data.get('priority')
    
    if priority not in valid_priorities:
        return jsonify({'error': f'Invalid priority. Must be one of: {", ".join(valid_priorities)}'}), 400
    
    mongo.db.support_tickets.update_one(
        {'_id': ObjectId(ticket_id)},
        {
            '$set': {
                'priority': priority,
                'updated_at': datetime.datetime.now(datetime.timezone.utc)
            }
        }
    )
    
    return jsonify({'message': 'Ticket priority updated'}), 200


@support_bp.route('/tickets/<ticket_id>', methods=['DELETE'])
@jwt_required()
def delete_ticket(ticket_id):
    """Delete a support ticket (user can only delete their own unopened tickets)"""
    user_id = get_jwt_identity()
    
    try:
        ticket = mongo.db.support_tickets.find_one({'_id': ObjectId(ticket_id)})
    except:
        return jsonify({'error': 'Invalid ticket ID'}), 400
    
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    # Only ticket creator (unless admin) and only if not yet responded
    if str(ticket['user_id']) != user_id and user.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if len(ticket.get('messages', [])) > 1 and user.get('role') != 'admin':
        return jsonify({'error': 'Cannot delete ticket that has replies'}), 400
    
    mongo.db.support_tickets.delete_one({'_id': ObjectId(ticket_id)})
    
    return jsonify({'message': 'Ticket deleted'}), 200


# ════════════════════════════════════════════════════════════════
# SUPPORT ADMIN ENDPOINTS
# ════════════════════════════════════════════════════════════════

@support_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
def support_stats():
    """Get support system statistics (admin only)"""
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if user.get('role') != 'admin':
        return jsonify({'error': 'Only admins can view stats'}), 403
    
    open_tickets = mongo.db.support_tickets.count_documents({'status': 'open'})
    in_progress = mongo.db.support_tickets.count_documents({'status': 'in_progress'})
    resolved = mongo.db.support_tickets.count_documents({'status': 'resolved'})
    closed = mongo.db.support_tickets.count_documents({'status': 'closed'})
    
    high_priority = mongo.db.support_tickets.count_documents({
        'priority': {'$in': ['high', 'urgent']},
        'status': {'$in': ['open', 'in_progress']}
    })
    
    return jsonify({
        'open': open_tickets,
        'in_progress': in_progress,
        'resolved': resolved,
        'closed': closed,
        'high_priority_unresolved': high_priority,
        'total': open_tickets + in_progress + resolved + closed
    }), 200


@support_bp.route('/admin/tickets', methods=['GET'])
@jwt_required()
def admin_get_all_tickets():
    """Get all tickets with filtering (admin only)"""
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if user.get('role') != 'admin':
        return jsonify({'error': 'Only admins can view all tickets'}), 403
    
    status = request.args.get('status')
    priority = request.args.get('priority')
    assigned_to = request.args.get('assigned_to')
    search = request.args.get('search')
    
    query = {}
    
    if status:
        query['status'] = status
    if priority:
        query['priority'] = priority
    if assigned_to:
        query['assigned_to'] = ObjectId(assigned_to)
    if search:
        import re
        regex = re.compile(search, re.IGNORECASE)
        query['$or'] = [
            {'subject': regex},
            {'description': regex}
        ]
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    total = mongo.db.support_tickets.count_documents(query)
    tickets = list(mongo.db.support_tickets.find(query)
                   .sort('updated_at', -1)
                   .skip((page - 1) * limit)
                   .limit(limit))
    
    return jsonify({
        'tickets': serialize_list(tickets),
        'total': total,
        'meta': {
            'page': page,
            'limit': limit,
            'total': total,
            'has_more': (page * limit) < total
        }
    }), 200
