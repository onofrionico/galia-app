from datetime import datetime
from app.extensions import db

class ProductMaster(db.Model):
    __tablename__ = 'product_masters'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    unit_of_measure = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    products = db.relationship('Product', back_populates='product_master', lazy='dynamic')
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])
    
    __table_args__ = (
        db.Index('idx_product_masters_name', 'name'),
        db.Index('idx_product_masters_category', 'category'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'unit_of_measure': self.unit_of_measure,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by_user_id': self.created_by_user_id,
            'linked_products_count': self.products.count()
        }
    
    def __repr__(self):
        return f'<ProductMaster {self.name}>'
