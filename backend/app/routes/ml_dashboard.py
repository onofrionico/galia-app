from flask import Blueprint, request, jsonify
from app.utils.decorators import admin_required
from app.services.ml_accuracy_service import MLAccuracyService
from app.services.holiday_service import HolidayService
from app.services.alert_service import AlertService
from app.models.ml_tracking import MLModelVersion, PredictionAlert
from datetime import datetime, timedelta
from app.utils.jwt_utils import token_required

bp = Blueprint('ml_dashboard', __name__, url_prefix='/api/v1/ml/dashboard')

@bp.route('/accuracy', methods=['GET'])
@token_required
@admin_required
def get_accuracy_metrics(current_user):
    """Get overall accuracy metrics"""
    days = request.args.get('days', 30, type=int)
    
    metrics = MLAccuracyService.get_accuracy_metrics(days=days)
    
    return jsonify(metrics), 200

@bp.route('/accuracy/by-hour', methods=['GET'])
@token_required
@admin_required
def get_accuracy_by_hour(current_user):
    """Get accuracy metrics grouped by hour"""
    result = MLAccuracyService.get_accuracy_by_hour()
    return jsonify(result), 200

@bp.route('/accuracy/by-day', methods=['GET'])
@token_required
@admin_required
def get_accuracy_by_day(current_user):
    """Get accuracy metrics grouped by day of week"""
    result = MLAccuracyService.get_accuracy_by_day_of_week()
    return jsonify(result), 200

@bp.route('/accuracy/update', methods=['POST'])
@token_required
@admin_required
def update_accuracy(current_user):
    """Update accuracy for a specific date"""
    data = request.get_json()
    
    if not data or 'date' not in data:
        return jsonify({'error': 'date is required'}), 400
    
    try:
        date = datetime.fromisoformat(data['date']).date()
    except (ValueError, AttributeError):
        return jsonify({'error': 'Invalid date format'}), 400
    
    result = MLAccuracyService.update_accuracy_for_date(date)
    
    return jsonify(result), 200

@bp.route('/retrain-check', methods=['GET'])
@token_required
@admin_required
def check_retrain_needed(current_user):
    """Check if model should be retrained"""
    result = MLAccuracyService.should_retrain_model()
    return jsonify(result), 200

@bp.route('/model-versions', methods=['GET'])
@token_required
@admin_required
def get_model_versions(current_user):
    """Get all model versions"""
    versions = MLModelVersion.query.order_by(
        MLModelVersion.trained_at.desc()
    ).limit(10).all()
    
    return jsonify({
        'success': True,
        'versions': [v.to_dict() for v in versions]
    }), 200

@bp.route('/alerts', methods=['GET'])
@token_required
def get_alerts(current_user):
    """Get prediction alerts"""
    schedule_id = request.args.get('schedule_id', type=int)
    severity = request.args.get('severity')
    
    result = AlertService.get_active_alerts(
        schedule_id=schedule_id,
        severity=severity
    )
    
    return jsonify(result), 200

@bp.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@token_required
@admin_required
def acknowledge_alert(current_user, alert_id):
    """Acknowledge an alert"""
    result = AlertService.acknowledge_alert(alert_id, current_user.id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
@token_required
@admin_required
def resolve_alert(current_user, alert_id):
    """Resolve an alert"""
    result = AlertService.resolve_alert(alert_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@bp.route('/alerts/summary', methods=['GET'])
@token_required
def get_alert_summary(current_user):
    """Get alert summary by severity"""
    result = AlertService.get_alert_summary()
    return jsonify(result), 200

@bp.route('/alerts/check-schedule/<int:schedule_id>', methods=['POST'])
@token_required
@admin_required
def check_schedule_alerts(current_user, schedule_id):
    """Check a schedule for prediction discrepancies"""
    result = AlertService.check_schedule_predictions(schedule_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@bp.route('/holidays', methods=['GET'])
@token_required
def get_holidays(current_user):
    """Get all holidays"""
    year = request.args.get('year', type=int)
    result = HolidayService.get_all_holidays(year=year)
    return jsonify(result), 200

@bp.route('/holidays/initialize', methods=['POST'])
@token_required
@admin_required
def initialize_holidays(current_user):
    """Initialize Argentina holidays"""
    result = HolidayService.initialize_holidays()
    return jsonify(result), 200

@bp.route('/holidays', methods=['POST'])
@token_required
@admin_required
def add_special_event(current_user):
    """Add a special event"""
    data = request.get_json()
    
    if not data or 'date' not in data or 'name' not in data:
        return jsonify({'error': 'date and name are required'}), 400
    
    result = HolidayService.add_special_event(
        event_date=data['date'],
        name=data['name'],
        impact_multiplier=data.get('impact_multiplier', 1.0),
        notes=data.get('notes')
    )
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@bp.route('/holidays/<int:holiday_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_holiday(current_user, holiday_id):
    """Delete a holiday"""
    result = HolidayService.delete_holiday(holiday_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@bp.route('/stats', methods=['GET'])
@token_required
@admin_required
def get_dashboard_stats(current_user):
    """Get overall dashboard statistics"""
    # Get active model version
    active_model = MLModelVersion.query.filter_by(is_active=True).first()
    
    # Get accuracy metrics
    accuracy = MLAccuracyService.get_accuracy_metrics(days=30)
    
    # Get alert summary
    alerts = AlertService.get_alert_summary()
    
    # Check if retrain needed
    retrain_check = MLAccuracyService.should_retrain_model()
    
    return jsonify({
        'success': True,
        'model': active_model.to_dict() if active_model else None,
        'accuracy': accuracy if accuracy['success'] else None,
        'alerts': alerts['summary'] if alerts['success'] else None,
        'retrain_recommendation': retrain_check
    }), 200
