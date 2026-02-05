from app.extensions import db
from datetime import datetime

class MLModelVersion(db.Model):
    """Track ML model versions and training history"""
    __tablename__ = 'ml_model_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50), nullable=False)
    trained_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    training_records = db.Column(db.Integer, nullable=False)
    train_score = db.Column(db.Float)
    test_score = db.Column(db.Float)
    features_used = db.Column(db.JSON)
    hyperparameters = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'version': self.version,
            'trained_at': self.trained_at.isoformat(),
            'training_records': self.training_records,
            'train_score': self.train_score,
            'test_score': self.test_score,
            'features_used': self.features_used,
            'hyperparameters': self.hyperparameters,
            'is_active': self.is_active,
            'notes': self.notes
        }

class MLPredictionAccuracy(db.Model):
    """Track actual vs predicted values for model accuracy"""
    __tablename__ = 'ml_prediction_accuracy'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.Integer, nullable=False)
    
    # Predicted values
    predicted_sales_count = db.Column(db.Integer)
    predicted_sales_amount = db.Column(db.Numeric(10, 2))
    recommended_staff_count = db.Column(db.Integer)
    
    # Actual values
    actual_sales_count = db.Column(db.Integer)
    actual_sales_amount = db.Column(db.Numeric(10, 2))
    actual_staff_count = db.Column(db.Integer)
    
    # Accuracy metrics
    sales_count_error = db.Column(db.Float)
    sales_amount_error = db.Column(db.Float)
    staff_count_error = db.Column(db.Float)
    
    model_version = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('date', 'hour', name='unique_date_hour_accuracy'),
    )
    
    def calculate_errors(self):
        """Calculate prediction errors"""
        if self.actual_sales_count and self.predicted_sales_count:
            self.sales_count_error = abs(self.actual_sales_count - self.predicted_sales_count) / max(self.actual_sales_count, 1)
        
        if self.actual_sales_amount and self.predicted_sales_amount:
            self.sales_amount_error = abs(float(self.actual_sales_amount) - float(self.predicted_sales_amount)) / max(float(self.actual_sales_amount), 1)
        
        if self.actual_staff_count and self.recommended_staff_count:
            self.staff_count_error = abs(self.actual_staff_count - self.recommended_staff_count) / max(self.actual_staff_count, 1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': str(self.date),
            'hour': self.hour,
            'predicted_sales_count': self.predicted_sales_count,
            'predicted_sales_amount': float(self.predicted_sales_amount) if self.predicted_sales_amount else None,
            'recommended_staff_count': self.recommended_staff_count,
            'actual_sales_count': self.actual_sales_count,
            'actual_sales_amount': float(self.actual_sales_amount) if self.actual_sales_amount else None,
            'actual_staff_count': self.actual_staff_count,
            'sales_count_error': self.sales_count_error,
            'sales_amount_error': self.sales_amount_error,
            'staff_count_error': self.staff_count_error,
            'model_version': self.model_version
        }

class Holiday(db.Model):
    """Track holidays and special events"""
    __tablename__ = 'holidays'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50))  # national, local, special_event
    impact_multiplier = db.Column(db.Float, default=1.0)  # Expected sales multiplier
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': str(self.date),
            'name': self.name,
            'type': self.type,
            'impact_multiplier': self.impact_multiplier,
            'notes': self.notes
        }

class PredictionAlert(db.Model):
    """Alerts when predictions differ significantly from scheduled staff"""
    __tablename__ = 'prediction_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'))
    date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.Integer, nullable=False)
    
    recommended_staff = db.Column(db.Integer, nullable=False)
    scheduled_staff = db.Column(db.Integer, nullable=False)
    difference = db.Column(db.Integer, nullable=False)
    difference_percentage = db.Column(db.Float, nullable=False)
    
    severity = db.Column(db.String(20))  # low, medium, high, critical
    status = db.Column(db.String(20), default='pending')  # pending, acknowledged, resolved
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    acknowledged_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    schedule = db.relationship('Schedule', backref='prediction_alerts')
    acknowledger = db.relationship('User', foreign_keys=[acknowledged_by])
    
    def calculate_severity(self):
        """Calculate alert severity based on difference"""
        if abs(self.difference_percentage) >= 50:
            self.severity = 'critical'
        elif abs(self.difference_percentage) >= 30:
            self.severity = 'high'
        elif abs(self.difference_percentage) >= 15:
            self.severity = 'medium'
        else:
            self.severity = 'low'
    
    def to_dict(self):
        return {
            'id': self.id,
            'schedule_id': self.schedule_id,
            'date': str(self.date),
            'hour': self.hour,
            'recommended_staff': self.recommended_staff,
            'scheduled_staff': self.scheduled_staff,
            'difference': self.difference,
            'difference_percentage': self.difference_percentage,
            'severity': self.severity,
            'status': self.status,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'created_at': self.created_at.isoformat()
        }
