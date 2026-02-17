from app.extensions import db
from datetime import datetime

class AppSettings(db.Model):
    __tablename__ = 'app_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    primary_color = db.Column(db.String(7), default='#3B82F6')
    secondary_color = db.Column(db.String(7), default='#10B981')
    accent_color = db.Column(db.String(7), default='#F59E0B')
    logo_url = db.Column(db.String(500), nullable=True)
    cafeteria_name = db.Column(db.String(200), default='Galia')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'logo_url': self.logo_url,
            'cafeteria_name': self.cafeteria_name,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
