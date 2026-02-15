from app.extensions import db
from app.models.ml_tracking import MLPredictionAccuracy, MLModelVersion
from app.models.staffing_metrics import StaffingMetrics, StaffingPrediction
from datetime import datetime, timedelta
from sqlalchemy import func, and_

class MLAccuracyService:
    """Service for tracking and analyzing ML model accuracy"""
    
    @staticmethod
    def update_accuracy_for_date(date):
        """
        Compare predictions vs actual data for a specific date.
        Should be run daily after the day is complete.
        """
        updated_count = 0
        
        # Get all predictions for this date
        predictions = StaffingPrediction.query.filter_by(date=date).all()
        
        for pred in predictions:
            # Get actual metrics
            actual = StaffingMetrics.query.filter_by(
                date=date,
                hour=pred.hour
            ).first()
            
            if not actual:
                continue
            
            # Check if accuracy record exists
            accuracy = MLPredictionAccuracy.query.filter_by(
                date=date,
                hour=pred.hour
            ).first()
            
            if not accuracy:
                accuracy = MLPredictionAccuracy(
                    date=date,
                    hour=pred.hour
                )
                db.session.add(accuracy)
            
            # Update values
            accuracy.predicted_sales_count = pred.predicted_sales_count
            accuracy.predicted_sales_amount = pred.predicted_sales_amount
            accuracy.recommended_staff_count = pred.recommended_staff_count
            
            accuracy.actual_sales_count = actual.sales_count
            accuracy.actual_sales_amount = actual.sales_amount
            accuracy.actual_staff_count = actual.employees_scheduled
            
            accuracy.model_version = pred.model_version
            
            # Calculate errors
            accuracy.calculate_errors()
            
            updated_count += 1
        
        db.session.commit()
        
        return {
            'success': True,
            'date': str(date),
            'records_updated': updated_count
        }
    
    @staticmethod
    def get_accuracy_metrics(start_date=None, end_date=None, days=30):
        """
        Get accuracy metrics for a date range.
        Returns MAE, MAPE, and other statistics.
        """
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=days)
        
        # Get all accuracy records in range
        records = MLPredictionAccuracy.query.filter(
            and_(
                MLPredictionAccuracy.date >= start_date,
                MLPredictionAccuracy.date <= end_date,
                MLPredictionAccuracy.actual_sales_count.isnot(None)
            )
        ).all()
        
        if not records:
            return {
                'success': False,
                'error': 'No accuracy data available for this period'
            }
        
        # Calculate metrics
        total_records = len(records)
        
        # Sales count metrics
        sales_count_errors = [r.sales_count_error for r in records if r.sales_count_error is not None]
        avg_sales_count_error = sum(sales_count_errors) / len(sales_count_errors) if sales_count_errors else 0
        
        # Sales amount metrics
        sales_amount_errors = [r.sales_amount_error for r in records if r.sales_amount_error is not None]
        avg_sales_amount_error = sum(sales_amount_errors) / len(sales_amount_errors) if sales_amount_errors else 0
        
        # Staff count metrics
        staff_count_errors = [r.staff_count_error for r in records if r.staff_count_error is not None]
        avg_staff_count_error = sum(staff_count_errors) / len(staff_count_errors) if staff_count_errors else 0
        
        # Calculate MAE (Mean Absolute Error) for sales count
        sales_mae = sum([abs(r.actual_sales_count - r.predicted_sales_count) 
                        for r in records if r.actual_sales_count and r.predicted_sales_count]) / total_records
        
        # Calculate accuracy percentage (within ±2 sales)
        accurate_predictions = sum([1 for r in records 
                                   if r.actual_sales_count and r.predicted_sales_count 
                                   and abs(r.actual_sales_count - r.predicted_sales_count) <= 2])
        accuracy_percentage = (accurate_predictions / total_records) * 100
        
        return {
            'success': True,
            'period': {
                'start_date': str(start_date),
                'end_date': str(end_date),
                'total_records': total_records
            },
            'sales_count': {
                'mae': round(sales_mae, 2),
                'mape': round(avg_sales_count_error * 100, 2),
                'accuracy_within_2': round(accuracy_percentage, 2)
            },
            'sales_amount': {
                'mape': round(avg_sales_amount_error * 100, 2)
            },
            'staff_count': {
                'mape': round(avg_staff_count_error * 100, 2)
            }
        }
    
    @staticmethod
    def get_accuracy_by_hour():
        """Get accuracy metrics grouped by hour of day"""
        records = MLPredictionAccuracy.query.filter(
            MLPredictionAccuracy.actual_sales_count.isnot(None)
        ).all()
        
        if not records:
            return {'success': False, 'error': 'No data available'}
        
        # Group by hour
        by_hour = {}
        for r in records:
            if r.hour not in by_hour:
                by_hour[r.hour] = []
            if r.sales_count_error is not None:
                by_hour[r.hour].append(r.sales_count_error)
        
        # Calculate average error per hour
        result = []
        for hour in sorted(by_hour.keys()):
            errors = by_hour[hour]
            result.append({
                'hour': hour,
                'avg_error_percentage': round(sum(errors) / len(errors) * 100, 2),
                'sample_size': len(errors)
            })
        
        return {
            'success': True,
            'by_hour': result
        }
    
    @staticmethod
    def get_accuracy_by_day_of_week():
        """Get accuracy metrics grouped by day of week"""
        # Join with staffing_metrics to get day_of_week
        query = db.session.query(
            StaffingMetrics.day_of_week,
            func.avg(MLPredictionAccuracy.sales_count_error).label('avg_error'),
            func.count(MLPredictionAccuracy.id).label('count')
        ).join(
            MLPredictionAccuracy,
            and_(
                StaffingMetrics.date == MLPredictionAccuracy.date,
                StaffingMetrics.hour == MLPredictionAccuracy.hour
            )
        ).filter(
            MLPredictionAccuracy.actual_sales_count.isnot(None)
        ).group_by(
            StaffingMetrics.day_of_week
        ).all()

        if not query:
            return {'success': False, 'error': 'No data available'}
        
        days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        result = []
        for day_num, avg_error, count in query:
            result.append({
                'day_of_week': day_num,
                'day_name': days[day_num],
                'avg_error_percentage': round(float(avg_error) * 100, 2) if avg_error else 0,
                'sample_size': count
            })
        
        return {
            'success': True,
            'by_day': result
        }
    
    @staticmethod
    def should_retrain_model():
        """
        Determine if model should be retrained based on accuracy degradation.
        Returns True if recent accuracy is significantly worse than historical.
        """
        # Get recent accuracy (last 7 days)
        recent = MLAccuracyService.get_accuracy_metrics(days=7)
        
        # Get historical accuracy (30 days ago to 7 days ago)
        end_date = datetime.now().date() - timedelta(days=7)
        start_date = end_date - timedelta(days=30)
        historical = MLAccuracyService.get_accuracy_metrics(start_date=start_date, end_date=end_date)
        
        if not recent['success'] or not historical['success']:
            recommendation = (
                recent.get('error')
                or historical.get('error')
                or 'Insufficient data for comparison'
            )

            return {
                'should_retrain': False,
                'recent_mape': recent.get('sales_count', {}).get('mape') if recent.get('success') else None,
                'historical_mape': historical.get('sales_count', {}).get('mape') if historical.get('success') else None,
                'degradation_percentage': 0,
                'recommendation': recommendation
            }
        
        recent_mape = recent['sales_count']['mape']
        historical_mape = historical['sales_count']['mape']
        
        # If recent error is 20% worse than historical, recommend retraining
        degradation = ((recent_mape - historical_mape) / historical_mape) * 100 if historical_mape > 0 else 0
        
        should_retrain = degradation > 20
        
        return {
            'should_retrain': should_retrain,
            'recent_mape': recent_mape,
            'historical_mape': historical_mape,
            'degradation_percentage': round(degradation, 2),
            'recommendation': 'Model accuracy has degraded significantly. Retraining recommended.' if should_retrain else 'Model accuracy is stable.'
        }
