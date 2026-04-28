from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import datetime
from bson import ObjectId

from app import mongo, serialize, serialize_list

conversations_bp = Blueprint('conversations', __name__, url_prefix='/api/conversations')

def get_current_user():
    user_id = get_jwt_identity()
    return mongo.db.users.find_one({"_id": ObjectId(user_id)})

@conversations_bp.route('/', methods=['GET'])
@jwt_required()
def get_conversations():
    """Return all conversations for the current user."""
    current_user = get_current_user()
    search = request.args.get('search', '').strip()
    user_id_str = str(current_user['_id'])

    # Find conversations where current user is a participant
    query = {"participant_ids": user_id_str}
    
    conversations = list(mongo.db.conversations.find(query).sort("last_message_at", -1))
    
    result = []
    for conv in conversations:
        c_dict = serialize(conv)
        other_user_id = [uid for uid in c_dict.get('participant_ids', []) if uid != user_id_str]
        other_user = None
        if other_user_id:
            other_user = mongo.db.users.find_one({"_id": ObjectId(other_user_id[0])})
        
        # filter by search
        if search and other_user:
            if search.lower() not in other_user.get('full_name', '').lower():
                continue
                
        c_dict['other_user'] = serialize(other_user) if other_user else None
        
        # Unread count
        c_dict['unread_count'] = c_dict.get('unread_counts', {}).get(user_id_str, 0)
        result.append(c_dict)

    return jsonify({'conversations': result}), 200

@conversations_bp.route('/<conversation_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(conversation_id):
    """Return paginated messages for a conversation."""
    current_user = get_current_user()
    user_id_str = str(current_user['_id'])
    
    conversation = mongo.db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
        
    if user_id_str not in conversation.get('participant_ids', []):
        return jsonify({'error': 'Unauthorized'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = {"conversation_id": conversation_id}
    total = mongo.db.messages.count_documents(query)
    messages = list(mongo.db.messages.find(query).sort("created_at", 1).skip((page - 1) * per_page).limit(per_page))

    return jsonify({
        'messages': serialize_list(messages),
        'total': total,
        'page': page,
        'per_page': per_page
    }), 200

@conversations_bp.route('/', methods=['POST'])
@jwt_required()
def create_conversation():
    """Start a new conversation or return existing."""
    current_user = get_current_user()
    user_id_str = str(current_user['_id'])
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    other_user_id = data.get('user_id')
    offer_id = data.get('offer_id')

    if not other_user_id and not offer_id:
        return jsonify({'error': 'Must provide user_id or offer_id'}), 400

    if offer_id and not other_user_id:
        offer = mongo.db.offers.find_one({"_id": ObjectId(offer_id)})
        if not offer:
            return jsonify({'error': 'Offer not found'}), 404
        other_user_id = offer.get("client_id")

    if other_user_id == user_id_str:
        return jsonify({'error': 'Cannot start conversation with yourself'}), 400

    other_user = mongo.db.users.find_one({"_id": ObjectId(other_user_id)})
    if not other_user:
        return jsonify({'error': 'Other user not found'}), 404

    # Check if conversation already exists
    existing = mongo.db.conversations.find_one({
        "participant_ids": {"$all": [user_id_str, other_user_id]}
    })

    if existing:
        return jsonify({'conversation': serialize(existing)}), 200

    # Create new
    conv_doc = {
        "participant_ids": [user_id_str, other_user_id],
        "offer_id": offer_id,
        "last_message": "",
        "last_message_at": datetime.datetime.now(datetime.timezone.utc),
        "unread_counts": {user_id_str: 0, other_user_id: 0}
    }
    
    result = mongo.db.conversations.insert_one(conv_doc)
    conv_doc["_id"] = result.inserted_id

    return jsonify({'conversation': serialize(conv_doc)}), 201

@conversations_bp.route('/<conversation_id>/messages', methods=['POST'])
@jwt_required()
def send_message(conversation_id):
    """Send a message to a conversation."""
    current_user = get_current_user()
    user_id_str = str(current_user['_id'])
    
    conversation = mongo.db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404

    if user_id_str not in conversation.get('participant_ids', []):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Message content required'}), 400

    # Mark other's messages as read
    mongo.db.messages.update_many(
        {
            "conversation_id": conversation_id,
            "sender_id": {"$ne": user_id_str},
            "is_read": False
        },
        {"$set": {"is_read": True}}
    )

    # Create message
    msg_doc = {
        "conversation_id": conversation_id,
        "sender_id": user_id_str,
        "content": content,
        "is_read": False,
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    msg_result = mongo.db.messages.insert_one(msg_doc)
    msg_doc["_id"] = msg_result.inserted_id

    # Update conversation
    other_user_id = [uid for uid in conversation.get("participant_ids", []) if uid != user_id_str][0]
    
    mongo.db.conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$set": {
                "last_message": content,
                "last_message_at": datetime.datetime.now(datetime.timezone.utc),
                f"unread_counts.{user_id_str}": 0
            },
            "$inc": {
                f"unread_counts.{other_user_id}": 1
            }
        }
    )

    return jsonify({'message': serialize(msg_doc)}), 201
