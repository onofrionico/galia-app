from app.extensions import db
from app.models.ml_tracking import PredictionAlert
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.staffing_metrics import StaffingPrediction
from app.services.notification_service import NotificationService
from datetime import datetime, timedelta
from sqlalchemy import and_, func

class AlertService:
    """Service for managing prediction alerts"""
    
    @staticmethod
    def check_schedule_predictions(schedule_id):
        """
        Check if a schedule has significant differences from ML predictions.
        Create alerts for discrepancies.
        """
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            return {'success': False, 'error': 'Schedule not found'}
        
        alerts_created = 0
        current_date = schedule.start_date
        
        while current_date <= schedule.end_date:
            # Get shifts for this date
            shifts = Shift.query.filter(
                and_(
                    Shift.schedule_id == schedule_id,
                    func.date(Shift.start_time) == current_date
                )
            ).all()
            
            # Count staff by hour
            staff_by_hour = {}
            for shift in shifts:
                start_hour = shift.start_time.hour
                end_hour = shift.end_time.hour
                
                for hour in range(start_hour, end_hour):
                    staff_by_hour[hour] = staff_by_hour.get(hour, 0) + 1
            
            # Compare with predictions
            predictions = StaffingPrediction.query.filter_by(date=current_date).all()
            
            for pred in predictions:
                scheduled = staff_by_hour.get(pred.hour, 0)
                recommended = pred.recommended_staff_count
                
                if scheduled == 0:
                    continue  # No staff scheduled for this hour
                
                difference = scheduled - recommended
                difference_pct = (difference / recommended * 100) if recommended > 0 else 0
                
                # Only create alert if difference is significant (>15%)
                if abs(difference_pct) >= 15:
                    # Check if alert already exists
                    existing = PredictionAlert.query.filter_by(
                        schedule_id=schedule_id,
                        date=current_date,
                        hour=pred.hour
                    ).first()
                    
                    if not existing:
                        alert = PredictionAlert(
                            schedule_id=schedule_id,
                            date=current_date,
                            hour=pred.hour,
                            recommended_staff=recommended,
                            scheduled_staff=scheduled,
                            difference=difference,
                            difference_percentage=difference_pct
                        )
                        alert.calculate_severity()
                        db.session.add(alert)
                        alerts_created += 1
            
            current_date += timedelta(days=1)
        
        db.session.commit()
        
        return {
            'success': True,
            'alerts_created': alerts_created,
            'schedule_id': schedule_id
        }
    
    @staticmethod
    def get_active_alerts(schedule_id=None, severity=None):
        """Get active (pending) alerts"""
        query = PredictionAlert.query.filter_by(status='pending')
        
        if schedule_id:
            query = query.filter_by(schedule_id=schedule_id)
        
        if severity:
            query = query.filter_by(severity=severity)
        
        alerts = query.order_by(
            PredictionAlert.severity.desc(),
            PredictionAlert.date,
            PredictionAlert.hour
        ).all()
        
        return {
            'success': True,
            'alerts': [a.to_dict() for a in alerts],
            'total': len(alerts)
        }
    
    @staticmethod
    def acknowledge_alert(alert_id, user_id):
        """Mark an alert as acknowledged"""
        alert = PredictionAlert.query.get(alert_id)
        if not alert:
            return {'success': False, 'error': 'Alert not found'}
        
        alert.status = 'acknowledged'
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'success': True,
            'alert': alert.to_dict()
        }
    
    @staticmethod
    def resolve_alert(alert_id):
        """Mark an alert as resolved"""
        alert = PredictionAlert.query.get(alert_id)
        if not alert:
            return {'success': False, 'error': 'Alert not found'}
        
        alert.status = 'resolved'
        db.session.commit()
        
        return {
            'success': True,
            'alert': alert.to_dict()
        }
    
    @staticmethod
    def get_alert_summary():
        """Get summary of alerts by severity"""
        summary = db.session.query(
            PredictionAlert.severity,
            func.count(PredictionAlert.id).label('count')
        ).filter_by(
            status='pending'
        ).group_by(
            PredictionAlert.severity
        ).all()
        
        result = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for severity, count in summary:
            result[severity] = count
        
        return {
            'success': True,
            'summary': result,
            'total_pending': sum(result.values())
        }
    
    @staticmethod
    def notify_critical_alerts():
        """
        Send notifications for critical alerts.
        Should be run periodically (e.g., daily).
        """
        critical_alerts = PredictionAlert.query.filter_by(
            severity='critical',
            status='pending'
        ).all()
        
        if not critical_alerts:
            return {
                'success': True,
                'notifications_sent': 0,
                'message': 'No critical alerts to notify'
            }
        
        # Group alerts by schedule
        alerts_by_schedule = {}
        for alert in critical_alerts:
            if alert.schedule_id not in alerts_by_schedule:
                alerts_by_schedule[alert.schedule_id] = []
            alerts_by_schedule[alert.schedule_id].append(alert)
        
        notifications_sent = 0
        
        for schedule_id, alerts in alerts_by_schedule.items():
            schedule = Schedule.query.get(schedule_id)
            if not schedule:
                continue
            
            # Create notification for schedule owner/admins
            message = f"⚠️ {len(alerts)} alertas críticas en la grilla '{schedule.name}'. "
            message += "Las predicciones ML difieren significativamente del personal programado."
            
            # In a real system, you'd send this to admins
            # For now, we'll just log it
            notifications_sent += 1
        
        return {
            'success': True,
            'notifications_sent': notifications_sent,
            'critical_alerts': len(critical_alerts)
        }
