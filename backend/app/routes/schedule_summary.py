from flask import Blueprint, request, jsonify
from app.utils.decorators import admin_required
from app.services.schedule_service import ScheduleService
from app.utils.jwt_utils import token_required

bp = Blueprint('schedule_summary', __name__, url_prefix='/api/v1/schedules')

@bp.route('/<int:schedule_id>/summary', methods=['GET'])
@token_required
@admin_required
def get_schedule_summary(current_user, schedule_id):
    """Get summary of hours and costs for a schedule"""
    cost_summary = ScheduleService.calculate_schedule_cost(schedule_id)
    hours_summary = ScheduleService.get_employee_hours_summary(schedule_id)
    
    return jsonify({
        'cost_summary': cost_summary,
        'hours_summary': hours_summary
    }), 200

@bp.route('/<int:schedule_id>/publish', methods=['POST'])
@token_required
@admin_required
def publish_schedule(current_user, schedule_id):
    """Publish a schedule"""
    schedule = ScheduleService.publish_schedule(schedule_id)
    
    if not schedule:
        return jsonify({'error': 'Grilla no encontrada'}), 404
    
    return jsonify({
        'message': 'Grilla publicada exitosamente',
        'schedule': schedule.to_dict(include_shifts=True)
    }), 200
