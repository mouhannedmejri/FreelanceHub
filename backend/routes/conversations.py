from flask import Blueprint, request, jsonify
from models import db, Conversation, Message, User, Offer
from routes.auth import token_required
from datetime import datetime, timezone
from sqlalchemy import or_, and_

conversations_bp = Blueprint('conversations', __name__, url_prefix='/api/conversations')

@conversations_bp.route('/', methods=['GET'])
@token_required
def get_conversations(current_user):
    """Return all conversations for the current user."""
    search = request.args.get('search', '').strip()

    # Get conversations where current user is participant 1 or 2
    query = Conversation.query.filter(
        or_(
            Conversation.participant_1_id == current_user.id,
            Conversation.participant_2_id == current_user.id
        )
    )

    if search:
        like_term = f'%{search}%'
        # Need to join with User to search by name of the *other* participant
        # But for simplicity, let's fetch all and filter in python if search is present,
        # or join both. Let's join and filter.
        query = query.join(User, or_(
            and_(Conversation.participant_1_id == User.id, Conversation.participant_1_id != current_user.id),
            and_(Conversation.participant_2_id == User.id, Conversation.participant_2_id != current_user.id)
        )).filter(User.full_name.ilike(like_term))

    conversations = query.order_by(Conversation.last_message_at.desc()).all()
    
    result = []
    for conv in conversations:
        c_dict = conv.to_dict()
        # Determine the other participant
        other_user = c_dict['participant_2'] if conv.participant_1_id == current_user.id else c_dict['participant_1']
        c_dict['other_user'] = other_user
        
        # Set unread count for current user
        c_dict['unread_count'] = conv.unread_count_p1 if conv.participant_1_id == current_user.id else conv.unread_count_p2
        
        result.append(c_dict)

    return jsonify({'conversations': result}), 200

@conversations_bp.route('/<int:conversation_id>/messages', methods=['GET'])
@token_required
def get_messages(current_user, conversation_id):
    """Return paginated messages for a conversation."""
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
        
    if conversation.participant_1_id != current_user.id and conversation.participant_2_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.asc())
    
    total = query.count()
    messages = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'messages': [m.to_dict() for m in messages],
        'total': total,
        'page': page,
        'per_page': per_page
    }), 200

@conversations_bp.route('/', methods=['POST'])
@token_required
def create_conversation(current_user):
    """Start a new conversation or return existing."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    other_user_id = data.get('user_id')
    offer_id = data.get('offer_id')

    if not other_user_id and not offer_id:
        return jsonify({'error': 'Must provide user_id or offer_id'}), 400

    if offer_id and not other_user_id:
        offer = Offer.query.get(offer_id)
        if not offer:
            return jsonify({'error': 'Offer not found'}), 404
        other_user_id = offer.client_id

    if other_user_id == current_user.id:
        return jsonify({'error': 'Cannot start conversation with yourself'}), 400

    other_user = User.query.get(other_user_id)
    if not other_user:
        return jsonify({'error': 'Other user not found'}), 404

    # Check if conversation already exists
    existing = Conversation.query.filter(
        or_(
            and_(Conversation.participant_1_id == current_user.id, Conversation.participant_2_id == other_user_id),
            and_(Conversation.participant_1_id == other_user_id, Conversation.participant_2_id == current_user.id)
        )
    ).first()

    if existing:
        return jsonify({'conversation': existing.to_dict()}), 200

    # Create new
    conv = Conversation(
        participant_1_id=current_user.id,
        participant_2_id=other_user_id,
        offer_id=offer_id,
        last_message='',
        last_message_at=datetime.now(timezone.utc)
    )
    db.session.add(conv)
    db.session.commit()

    return jsonify({'conversation': conv.to_dict()}), 201

@conversations_bp.route('/<int:conversation_id>/messages', methods=['POST'])
@token_required
def send_message(current_user, conversation_id):
    """Send a message to a conversation."""
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404

    if conversation.participant_1_id != current_user.id and conversation.participant_2_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Message content required'}), 400

    # Mark other's messages as read
    Message.query.filter(
        and_(
            Message.conversation_id == conversation_id,
            Message.sender_id != current_user.id,
            Message.is_read == False
        )
    ).update({'is_read': True})

    # Create message
    msg = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=content
    )
    db.session.add(msg)

    # Update conversation
    conversation.last_message = content
    conversation.last_message_at = datetime.now(timezone.utc)
    
    if conversation.participant_1_id == current_user.id:
        conversation.unread_count_p1 = 0
        conversation.unread_count_p2 += 1
    else:
        conversation.unread_count_p2 = 0
        conversation.unread_count_p1 += 1

    db.session.commit()

    return jsonify({'message': msg.to_dict()}), 201
