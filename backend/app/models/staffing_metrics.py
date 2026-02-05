from app.extensions import db
from datetime import datetime

class StaffingMetrics(db.Model):
    """
    Model to collect historical data for future ML-based staffing predictions.
    Tracks actual sales and employee count per hour to learn patterns.
    """
    __tablename__ = 'staffing_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    hour = db.Column(db.Integer, nullable=False)  # 0-23
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    employees_scheduled = db.Column(db.Integer, nullable=False)
    employees_present = db.Column(db.Integer, nullable=True)  # Can be updated later
    sales_count = db.Column(db.Integer, default=0)
    sales_amount = db.Column(db.Numeric(10, 2), default=0)
    is_holiday = db.Column(db.Boolean, default=False)
    weather_condition = db.Column(db.String(50), nullable=True)  # For future enhancement
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_staffing_date_hour', 'date', 'hour'),
        db.Index('idx_staffing_day_hour', 'day_of_week', 'hour'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': str(self.date),
            'hour': self.hour,
            'day_of_week': self.day_of_week,
            'employees_scheduled': self.employees_scheduled,
            'employees_present': self.employees_present,
            'sales_count': self.sales_count,
            'sales_amount': float(self.sales_amount) if self.sales_amount else 0,
            'is_holiday': self.is_holiday,
            'weather_condition': self.weather_condition,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StaffingPrediction(db.Model):
    """
    Model to store ML-based staffing predictions.
    This will be populated by a future ML service.
    """
    __tablename__ = 'staffing_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    hour = db.Column(db.Integer, nullable=False)
    predicted_sales_count = db.Column(db.Integer, nullable=False)
    predicted_sales_amount = db.Column(db.Numeric(10, 2), nullable=False)
    recommended_staff_count = db.Column(db.Integer, nullable=False)
    confidence_score = db.Column(db.Float, nullable=True)  # 0-1
    model_version = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.Index('idx_prediction_date_hour', 'date', 'hour'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': str(self.date),
            'hour': self.hour,
            'predicted_sales_count': self.predicted_sales_count,
            'predicted_sales_amount': float(self.predicted_sales_amount),
            'recommended_staff_count': self.recommended_staff_count,
            'confidence_score': self.confidence_score,
            'model_version': self.model_version,
            'created_at': self.created_at.isoformat()
        }
