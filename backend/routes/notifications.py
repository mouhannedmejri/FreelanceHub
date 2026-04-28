from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import datetime
from bson import ObjectId

from app import mongo, serialize, serialize_list

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    """Return all notifications for current user, newest first."""
    user_id = get_jwt_identity()
    notifications = list(mongo.db.notifications.find({"user_id": user_id}).sort("created_at", -1))
    return jsonify({
        'notifications': serialize_list(notifications),
        'unread_count': sum(1 for n in notifications if not n.get('is_read')),
    }), 200

@notifications_bp.route('/<notification_id>/read', methods=['PATCH'])
@jwt_required()
def mark_as_read(notification_id):
    """Mark a single notification as read."""
    user_id = get_jwt_identity()
    
    result = mongo.db.notifications.update_one(
        {"_id": ObjectId(notification_id), "user_id": user_id},
        {"$set": {"is_read": True}}
    )
    
    if result.matched_count == 0:
        return jsonify({'error': 'Notification not found'}), 404

    notification = mongo.db.notifications.find_one({"_id": ObjectId(notification_id)})
    return jsonify({'notification': serialize(notification)}), 200

@notifications_bp.route('/read-all', methods=['PATCH', 'POST'])
@jwt_required()
def mark_all_as_read():
    """Mark all notifications for current user as read."""
    user_id = get_jwt_identity()
    mongo.db.notifications.update_many(
        {"user_id": user_id, "is_read": False},
        {"$set": {"is_read": True}}
    )
    return jsonify({'message': 'All notifications marked as read'}), 200

@notifications_bp.route('/<notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """Delete a single notification."""
    user_id = get_jwt_identity()
    result = mongo.db.notifications.delete_one({"_id": ObjectId(notification_id), "user_id": user_id})

    if result.deleted_count == 0:
        return jsonify({'error': 'Notification not found'}), 404

    return jsonify({'message': 'Notification deleted'}), 200

def seed_notifications_for_user(user_doc):
    """Seed 4 sample notifications for a newly registered user."""
    now = datetime.datetime.now(datetime.timezone.utc)
    user_id = str(user_doc["_id"])
    samples = [
        {
            'user_id': user_id,
            'type': 'message',
            'title': 'Nouveau message reçu',
            'body': 'Un client vous a envoyé un message concernant votre profil.',
            'is_read': False,
            'created_at': now - datetime.timedelta(minutes=5),
        },
        {
            'user_id': user_id,
            'type': 'offer',
            'title': 'Nouvelle offre disponible',
            'body': 'Une offre correspondant à vos compétences a été publiée.',
            'is_read': False,
            'created_at': now - datetime.timedelta(hours=2),
        },
        {
            'user_id': user_id,
            'type': 'payment',
            'title': 'Paiement reçu',
            'body': 'Vous avez reçu un paiement de 150€ pour votre dernière mission.',
            'is_read': False,
            'created_at': now - datetime.timedelta(days=1),
        },
        {
            'user_id': user_id,
            'type': 'review',
            'title': 'Nouvel avis client',
            'body': 'Un client vous a laissé un avis 5 étoiles. Félicitations!',
            'is_read': False,
            'created_at': now - datetime.timedelta(days=3),
        },
    ]

    mongo.db.notifications.insert_many(samples)
