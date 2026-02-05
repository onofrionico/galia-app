from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.notification_service import NotificationService

bp = Blueprint('notifications', __name__, url_prefix='/api/v1/notifications')

@bp.route('', methods=['GET'])
@login_required
def get_notifications():
    """Get notifications for current user"""
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    notifications = NotificationService.get_user_notifications(current_user.id, unread_only)
    
    return jsonify([n.to_dict() for n in notifications]), 200

@bp.route('/<int:notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notification_id):
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
@login_required
def mark_all_read():
    """Mark all notifications as read for current user"""
    NotificationService.mark_all_as_read(current_user.id)
    
    return jsonify({'message': 'Todas las notificaciones marcadas como leídas'}), 200

@bp.route('/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """Get count of unread notifications"""
    notifications = NotificationService.get_user_notifications(current_user.id, unread_only=True)
    
    return jsonify({'count': len(notifications)}), 200
