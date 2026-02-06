from flask import Blueprint, request, jsonify
from app.utils.decorators import admin_required
from app.ml.staffing_predictor import StaffingPredictor
from app.models.staffing_metrics import StaffingPrediction
from datetime import datetime, timedelta
from sqlalchemy import and_
from app.utils.jwt_utils import token_required

bp = Blueprint('ml_predictions', __name__, url_prefix='/api/v1/ml')

@bp.route('/train', methods=['POST'])
@token_required
@admin_required
def train_model(current_user):
    """
    Train the ML model with historical data.
    Admin only endpoint.
    """
    data = request.get_json() or {}
    min_weeks = data.get('min_weeks', 8)
    
    predictor = StaffingPredictor()
    result = predictor.train(min_weeks=min_weeks)
    
    if result['success']:
        return jsonify({
            'message': 'Modelo entrenado exitosamente',
            'details': result
        }), 200
    else:
        return jsonify({
            'error': 'Error al entrenar el modelo',
            'details': result
        }), 400

@bp.route('/predict', methods=['POST'])
@token_required
@admin_required
def generate_predictions(current_user):
    """
    Generate predictions for a date range.
    Admin only endpoint.
    """
    data = request.get_json()
    
    if not data or 'start_date' not in data or 'end_date' not in data:
        return jsonify({'error': 'start_date y end_date son requeridos'}), 400
    
    try:
        start_date = datetime.fromisoformat(data['start_date']).date()
        end_date = datetime.fromisoformat(data['end_date']).date()
    except (ValueError, AttributeError):
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    if end_date < start_date:
        return jsonify({'error': 'end_date debe ser mayor o igual a start_date'}), 400
    
    # Limit to 30 days
    if (end_date - start_date).days > 30:
        return jsonify({'error': 'El rango máximo es de 30 días'}), 400
    
    predictor = StaffingPredictor()
    result = predictor.generate_predictions(start_date, end_date)
    
    if result['success']:
        return jsonify({
            'message': 'Predicciones generadas exitosamente',
            'details': result
        }), 200
    else:
        return jsonify({
            'error': 'Error al generar predicciones',
            'details': result
        }), 400

@bp.route('/recommendations', methods=['GET'])
@token_required
def get_recommendations(current_user):
    """
    Get staffing recommendations for a date range.
    Returns predictions grouped by date and hour.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'start_date y end_date son requeridos'}), 400
    
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
    except (ValueError, AttributeError):
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    # Get predictions from database
    predictions = StaffingPrediction.query.filter(
        and_(
            StaffingPrediction.date >= start,
            StaffingPrediction.date <= end
        )
    ).order_by(StaffingPrediction.date, StaffingPrediction.hour).all()
    
    # Group by date
    result = {}
    for pred in predictions:
        date_str = str(pred.date)
        if date_str not in result:
            result[date_str] = []
        
        result[date_str].append({
            'hour': pred.hour,
            'predicted_sales_count': pred.predicted_sales_count,
            'predicted_sales_amount': float(pred.predicted_sales_amount),
            'recommended_staff_count': pred.recommended_staff_count,
            'confidence_score': pred.confidence_score
        })
    
    return jsonify(result), 200

@bp.route('/recommendations/summary', methods=['GET'])
@token_required
def get_recommendations_summary(current_user):
    """
    Get summary of recommendations for a date range.
    Useful for quick overview when creating schedules.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'start_date y end_date son requeridos'}), 400
    
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
    except (ValueError, AttributeError):
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    predictions = StaffingPrediction.query.filter(
        and_(
            StaffingPrediction.date >= start,
            StaffingPrediction.date <= end
        )
    ).all()
    
    if not predictions:
        return jsonify({
            'message': 'No hay predicciones disponibles para este período',
            'has_predictions': False
        }), 200
    
    # Calculate daily summaries
    daily_summary = {}
    for pred in predictions:
        date_str = str(pred.date)
        if date_str not in daily_summary:
            daily_summary[date_str] = {
                'date': date_str,
                'total_predicted_sales': 0,
                'total_predicted_amount': 0,
                'peak_hour': None,
                'peak_staff_needed': 0,
                'avg_staff_needed': 0,
                'staff_hours': []
            }
        
        daily_summary[date_str]['total_predicted_sales'] += pred.predicted_sales_count
        daily_summary[date_str]['total_predicted_amount'] += float(pred.predicted_sales_amount)
        daily_summary[date_str]['staff_hours'].append(pred.recommended_staff_count)
        
        if pred.recommended_staff_count > daily_summary[date_str]['peak_staff_needed']:
            daily_summary[date_str]['peak_staff_needed'] = pred.recommended_staff_count
            daily_summary[date_str]['peak_hour'] = pred.hour
    
    # Calculate averages
    for date_str in daily_summary:
        staff_hours = daily_summary[date_str]['staff_hours']
        daily_summary[date_str]['avg_staff_needed'] = round(sum(staff_hours) / len(staff_hours), 1)
        daily_summary[date_str]['total_predicted_amount'] = round(
            daily_summary[date_str]['total_predicted_amount'], 2
        )
        del daily_summary[date_str]['staff_hours']
    
    return jsonify({
        'has_predictions': True,
        'daily_summary': list(daily_summary.values()),
        'model_version': predictions[0].model_version if predictions else None
    }), 200

@bp.route('/model/status', methods=['GET'])
@token_required
@admin_required
def get_model_status(current_user):
    """
    Get status of the ML model.
    """
    predictor = StaffingPredictor()
    model_loaded = predictor.load_models()
    
    if model_loaded:
        # Get latest prediction to check model version
        latest_pred = StaffingPrediction.query.order_by(
            StaffingPrediction.created_at.desc()
        ).first()
        
        return jsonify({
            'model_trained': True,
            'model_version': predictor.model_version,
            'latest_prediction': latest_pred.created_at.isoformat() if latest_pred else None
        }), 200
    else:
        return jsonify({
            'model_trained': False,
            'message': 'El modelo aún no ha sido entrenado'
        }), 200
