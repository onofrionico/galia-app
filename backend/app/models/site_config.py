from datetime import datetime

from app.extensions import db


class SiteConfig(db.Model):
    """Site configuration for branding and display settings (logo and banner background paths)"""

    __tablename__ = 'site_config'

    id = db.Column(db.Integer, primary_key=True)
    logo_path = db.Column(db.String(255), nullable=True)
    banner_background_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'logo_path': self.logo_path,
            'banner_background_path': self.banner_background_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<SiteConfig id={self.id}>'
