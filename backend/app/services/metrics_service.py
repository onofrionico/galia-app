from app.extensions import db
from app.models.staffing_metrics import StaffingMetrics
from app.models.shift import Shift
from app.models.sale import Sale
from datetime import datetime, timedelta
from collections import defaultdict

class MetricsService:
    """
    Service to collect and analyze staffing metrics for ML predictions.
    This data will be used in the future to train models for optimal staffing.
    """
    
    @staticmethod
    def collect_daily_metrics(date):
        """
        Collect metrics for a specific date.
        Should be run at the end of each day or in a batch process.
        """
        # Get all shifts for the date
        shifts = Shift.query.filter_by(shift_date=date).all()
        
        # Get all sales for the date
        sales = Sale.query.filter(
            db.func.date(Sale.created_at) == date
        ).all()
        
        # Calculate hourly metrics
        hourly_staff = defaultdict(int)
        hourly_sales_count = defaultdict(int)
        hourly_sales_amount = defaultdict(float)
        
        # Count staff per hour
        for shift in shifts:
            start_hour = shift.start_time.hour
            end_hour = shift.end_time.hour
            for hour in range(start_hour, end_hour):
                hourly_staff[hour] += 1
        
        # Count sales per hour
        for sale in sales:
            hour = sale.created_at.hour
            hourly_sales_count[hour] += 1
            hourly_sales_amount[hour] += float(sale.amount)
        
        # Create or update metrics for each hour
        day_of_week = date.weekday()
        
        for hour in range(24):
            metric = StaffingMetrics.query.filter_by(
                date=date,
                hour=hour
            ).first()
            
            if metric:
                # Update existing
                metric.employees_scheduled = hourly_staff.get(hour, 0)
                metric.sales_count = hourly_sales_count.get(hour, 0)
                metric.sales_amount = hourly_sales_amount.get(hour, 0)
                metric.updated_at = datetime.utcnow()
            else:
                # Create new
                metric = StaffingMetrics(
                    date=date,
                    hour=hour,
                    day_of_week=day_of_week,
                    employees_scheduled=hourly_staff.get(hour, 0),
                    sales_count=hourly_sales_count.get(hour, 0),
                    sales_amount=hourly_sales_amount.get(hour, 0)
                )
                db.session.add(metric)
        
        db.session.commit()
        return True
    
    @staticmethod
    def get_historical_patterns(day_of_week=None, hour=None, weeks_back=12):
        """
        Get historical patterns for analysis.
        Useful for understanding staffing needs before ML model is trained.
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=weeks_back)
        
        query = StaffingMetrics.query.filter(
            StaffingMetrics.date >= start_date,
            StaffingMetrics.date <= end_date
        )
        
        if day_of_week is not None:
            query = query.filter_by(day_of_week=day_of_week)
        
        if hour is not None:
            query = query.filter_by(hour=hour)
        
        metrics = query.all()
        
        if not metrics:
            return None
        
        # Calculate averages
        total_sales = sum(m.sales_count for m in metrics)
        total_amount = sum(float(m.sales_amount) for m in metrics)
        total_staff = sum(m.employees_scheduled for m in metrics)
        count = len(metrics)
        
        return {
            'average_sales_count': round(total_sales / count, 2),
            'average_sales_amount': round(total_amount / count, 2),
            'average_staff_count': round(total_staff / count, 2),
            'data_points': count,
            'period_start': str(start_date),
            'period_end': str(end_date)
        }
    
    @staticmethod
    def get_recommendations(date, hour):
        """
        Get staffing recommendations based on historical data.
        This is a simple rule-based approach until ML model is implemented.
        """
        day_of_week = date.weekday()
        
        # Get historical pattern for this day/hour
        pattern = MetricsService.get_historical_patterns(
            day_of_week=day_of_week,
            hour=hour,
            weeks_back=8
        )
        
        if not pattern or pattern['data_points'] < 3:
            return {
                'recommended_staff': 2,  # Default minimum
                'confidence': 'low',
                'reason': 'Insufficient historical data'
            }
        
        # Simple rule: 1 employee per 10 expected sales, minimum 1
        avg_sales = pattern['average_sales_count']
        recommended = max(1, round(avg_sales / 10))
        
        confidence = 'high' if pattern['data_points'] >= 8 else 'medium'
        
        return {
            'recommended_staff': recommended,
            'confidence': confidence,
            'expected_sales': round(avg_sales, 1),
            'expected_amount': round(pattern['average_sales_amount'], 2),
            'based_on_data_points': pattern['data_points']
        }
