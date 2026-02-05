from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models.shift import Shift
from app.models.employee import Employee
from sqlalchemy import func
from datetime import datetime, timedelta, time
from collections import defaultdict

bp = Blueprint('coverage', __name__, url_prefix='/api/v1/coverage')

@bp.route('/hourly', methods=['GET'])
@login_required
def get_hourly_coverage():
    """Get hourly coverage for a date range"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'start_date y end_date son requeridos'}), 400
    
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
    except (ValueError, AttributeError):
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    # Get all shifts in the date range
    shifts = Shift.query.filter(
        Shift.shift_date >= start,
        Shift.shift_date <= end
    ).all()
    
    # Calculate coverage by hour for each day
    coverage_data = defaultdict(lambda: defaultdict(int))
    
    for shift in shifts:
        date_str = str(shift.shift_date)
        
        # Get start and end hours
        start_hour = shift.start_time.hour
        end_hour = shift.end_time.hour
        
        # Count employee for each hour they work
        for hour in range(start_hour, end_hour):
            coverage_data[date_str][hour] += 1
    
    # Format response
    result = []
    current_date = start
    while current_date <= end:
        date_str = str(current_date)
        hourly_data = []
        
        for hour in range(24):
            hourly_data.append({
                'hour': hour,
                'employee_count': coverage_data[date_str].get(hour, 0)
            })
        
        result.append({
            'date': date_str,
            'hourly_coverage': hourly_data
        })
        
        current_date += timedelta(days=1)
    
    return jsonify(result), 200

@bp.route('/summary', methods=['GET'])
@login_required
def get_coverage_summary():
    """Get coverage summary statistics for a date range"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'start_date y end_date son requeridos'}), 400
    
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
    except (ValueError, AttributeError):
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    # Get all shifts in the date range
    shifts = Shift.query.filter(
        Shift.shift_date >= start,
        Shift.shift_date <= end
    ).all()
    
    # Calculate statistics
    total_shifts = len(shifts)
    total_hours = sum(float(shift.hours) for shift in shifts)
    unique_employees = len(set(shift.employee_id for shift in shifts))
    
    # Calculate peak hours
    hourly_counts = defaultdict(int)
    for shift in shifts:
        start_hour = shift.start_time.hour
        end_hour = shift.end_time.hour
        for hour in range(start_hour, end_hour):
            hourly_counts[hour] += 1
    
    peak_hour = max(hourly_counts.items(), key=lambda x: x[1]) if hourly_counts else (None, 0)
    
    return jsonify({
        'total_shifts': total_shifts,
        'total_hours': round(total_hours, 2),
        'unique_employees': unique_employees,
        'peak_hour': peak_hour[0],
        'peak_hour_count': peak_hour[1],
        'average_shifts_per_day': round(total_shifts / ((end - start).days + 1), 2)
    }), 200
