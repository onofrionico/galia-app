from datetime import datetime
from app.extensions import db

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    tax_id = db.Column(db.String(50), nullable=True, unique=True)
    contact_person = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    address = db.Column(db.Text, nullable=True)
    payment_terms = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    modified_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    products = db.relationship('Product', back_populates='supplier', lazy='dynamic', overlaps="supplier")
    purchases = db.relationship('Purchase', back_populates='supplier', lazy='dynamic', overlaps="supplier")
    created_by = db.relationship('User', foreign_keys=[created_by_user_id], overlaps="created_by,modified_by")
    modified_by = db.relationship('User', foreign_keys=[modified_by_user_id], overlaps="created_by,modified_by")
    
    __table_args__ = (
        db.Index('idx_suppliers_name', 'name'),
        db.Index('idx_suppliers_status', 'status'),
        db.Index('idx_suppliers_is_deleted', 'is_deleted'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'tax_id': self.tax_id,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'payment_terms': self.payment_terms,
            'status': self.status,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by_user_id': self.created_by_user_id,
            'modified_by_user_id': self.modified_by_user_id
        }
    
    def __repr__(self):
        return f'<Supplier {self.name} ({self.tax_id})>'
