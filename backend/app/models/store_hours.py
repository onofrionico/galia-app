from app.extensions import db
from datetime import datetime

class StoreHours(db.Model):
    """Configuración de horarios de trabajo del local"""
    __tablename__ = 'store_hours'
    
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Lunes, 6=Domingo
    opening_time = db.Column(db.Time, nullable=False)
    closing_time = db.Column(db.Time, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relaciones
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'location_name': self.location_name,
            'day_of_week': self.day_of_week,
            'day_name': self.get_day_name(),
            'opening_time': self.opening_time.strftime('%H:%M') if self.opening_time else None,
            'closing_time': self.closing_time.strftime('%H:%M') if self.closing_time else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_day_name(self):
        days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return days[self.day_of_week] if 0 <= self.day_of_week <= 6 else 'Desconocido'
    
    def __repr__(self):
        return f'<StoreHours {self.location_name} - {self.get_day_name()}>'
