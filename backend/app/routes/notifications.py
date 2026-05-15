from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.notification_preference import NotificationPreference
from app.services.notification_service import NotificationService
from app.utils.jwt_utils import token_required

bp = Blueprint('notifications', __name__, url_prefix='/api/v1/notifications')

@bp.route('', methods=['GET'])
@token_required
def get_notifications(current_user):
    """Get notifications for current user"""
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    notifications = NotificationService.get_user_notifications(current_user.id, unread_only)
    
    return jsonify([n.to_dict() for n in notifications]), 200

@bp.route('/<int:notification_id>/read', methods=['PUT'])
@token_required
def mark_notification_read(current_user, notification_id):
    """Mark a notification as read"""
    notification = NotificationService.mark_as_read(notification_id)
    
    if not notification:
        return jsonify({'error': 'Notificación no encontrada'}), 404
    
    if notification.user_id != current_user.id:
        return jsonify({'error': 'No autorizado'}), 403
    
    return jsonify({
        'message': 'Notificación marcada como leída',
        'notification': notification.to_dict()
    }), 200

@bp.route('/mark-all-read', methods=['PUT'])
@token_required
def mark_all_read(current_user):
    """Mark all notifications as read for current user"""
    NotificationService.mark_all_as_read(current_user.id)
    
    return jsonify({'message': 'Todas las notificaciones marcadas como leídas'}), 200

@bp.route('/unread-count', methods=['GET'])
@token_required
def get_unread_count(current_user):
    """Get count of unread notifications"""
    notifications = NotificationService.get_user_notifications(current_user.id, unread_only=True)

    return jsonify({'count': len(notifications)}), 200

@bp.route('/preferences', methods=['GET'])
@token_required
def get_preferences(current_user):
    """Get notification preferences for current user"""
    prefs = NotificationPreference.query.filter_by(user_id=current_user.id).first()
    if not prefs:
        # Create default preferences
        prefs = NotificationPreference(
            user_id=current_user.id,
            comanda_enabled=True,
            venta_cerrada_enabled=True,
        )
        db.session.add(prefs)
        db.session.commit()

    return jsonify(prefs.to_dict()), 200

@bp.route('/preferences', methods=['PUT'])
@token_required
def update_preferences(current_user):
    """Update notification preferences for current user"""
    prefs = NotificationPreference.query.filter_by(user_id=current_user.id).first()
    if not prefs:
        prefs = NotificationPreference(user_id=current_user.id)

    data = request.get_json() or {}
    if 'comanda_enabled' in data:
        prefs.comanda_enabled = bool(data['comanda_enabled'])
    if 'venta_cerrada_enabled' in data:
        prefs.venta_cerrada_enabled = bool(data['venta_cerrada_enabled'])

    db.session.add(prefs)
    db.session.commit()

    return jsonify(prefs.to_dict()), 200
