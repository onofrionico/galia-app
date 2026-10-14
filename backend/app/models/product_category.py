from datetime import datetime
from app.extensions import db

class ProductCategory(db.Model):
    __tablename__ = 'product_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(20), nullable=True)
    icon = db.Column(db.String(10), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    fudo_category_id = db.Column(db.String(20), unique=True, nullable=True)
    fudo_status = db.Column(db.String(20), nullable=True)  # None | 'missing'
    # Estación de producción (comandas). Campo de Galia: la sincronización con Fudo no lo toca.
    station_id = db.Column(db.Integer, db.ForeignKey('print_stations.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    products = db.relationship('Product', backref='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'is_active': self.is_active,
            'fudo_category_id': self.fudo_category_id,
            'fudo_status': self.fudo_status,
            'station_id': self.station_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
