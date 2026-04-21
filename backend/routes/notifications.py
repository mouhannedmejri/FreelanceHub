from flask import Blueprint, request, jsonify
from models import db, Notification, NotificationTypeEnum
from routes.auth import token_required
import datetime

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@notifications_bp.route('/', methods=['GET'])
@token_required
def get_notifications(current_user):
    """Return all notifications for current user, newest first."""
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).all()
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': sum(1 for n in notifications if not n.is_read),
    }), 200


@notifications_bp.route('/<int:notification_id>/read', methods=['PATCH'])
@token_required
def mark_as_read(current_user, notification_id):
    """Mark a single notification as read."""
    notification = Notification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first()

    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    notification.is_read = True
    db.session.commit()
    return jsonify({'notification': notification.to_dict()}), 200


@notifications_bp.route('/read-all', methods=['PATCH', 'POST'])
@token_required
def mark_all_as_read(current_user):
    """Mark all notifications for current user as read."""
    Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read'}), 200


@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@token_required
def delete_notification(current_user, notification_id):
    """Delete a single notification."""
    notification = Notification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first()

    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    db.session.delete(notification)
    db.session.commit()
    return jsonify({'message': 'Notification deleted'}), 200


def seed_notifications_for_user(user):
    """Seed 4 sample notifications for a newly registered user."""
    now = datetime.datetime.now(datetime.timezone.utc)
    samples = [
        {
            'type': NotificationTypeEnum.message,
            'title': 'Nouveau message reçu',
            'body': 'Un client vous a envoyé un message concernant votre profil.',
            'created_at': now - datetime.timedelta(minutes=5),
        },
        {
            'type': NotificationTypeEnum.offer,
            'title': 'Nouvelle offre disponible',
            'body': 'Une offre correspondant à vos compétences a été publiée.',
            'created_at': now - datetime.timedelta(hours=2),
        },
        {
            'type': NotificationTypeEnum.payment,
            'title': 'Paiement reçu',
            'body': 'Vous avez reçu un paiement de 150€ pour votre dernière mission.',
            'created_at': now - datetime.timedelta(days=1),
        },
        {
            'type': NotificationTypeEnum.review,
            'title': 'Nouvel avis client',
            'body': 'Un client vous a laissé un avis 5 étoiles. Félicitations!',
            'created_at': now - datetime.timedelta(days=3),
        },
    ]

    for s in samples:
        notif = Notification(user_id=user.id, **s)
        db.session.add(notif)

    db.session.commit()
