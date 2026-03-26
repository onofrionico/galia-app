from datetime import datetime
from app.extensions import db

class Purchase(db.Model):
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    related_expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)
    purchase_date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='ARS')
    exchange_rate = db.Column(db.Numeric(12, 6), nullable=True)
    invoice_number = db.Column(db.String(100), nullable=True)
    cae_number = db.Column(db.String(100), nullable=True)
    payment_status = db.Column(db.String(20), nullable=False, default='pending')
    notes = db.Column(db.Text, nullable=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    modified_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    supplier = db.relationship('Supplier', back_populates='purchases')
    related_expense = db.relationship('Expense', foreign_keys=[related_expense_id])
    items = db.relationship('PurchaseItem', back_populates='purchase', lazy='dynamic', cascade='all, delete-orphan')
    price_history_entries = db.relationship('PriceHistory', back_populates='related_purchase', lazy='dynamic')
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])
    modified_by = db.relationship('User', foreign_keys=[modified_by_user_id])
    
    __table_args__ = (
        db.Index('idx_purchases_supplier_id', 'supplier_id'),
        db.Index('idx_purchases_purchase_date', 'purchase_date'),
        db.Index('idx_purchases_payment_status', 'payment_status'),
        db.Index('idx_purchases_is_deleted', 'is_deleted'),
        db.Index('idx_purchases_related_expense_id', 'related_expense_id'),
    )
    
    def to_dict(self, include_items=True, include_supplier=False):
        data = {
            'id': self.id,
            'supplier_id': self.supplier_id,
            'related_expense_id': self.related_expense_id,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'currency': self.currency,
            'exchange_rate': float(self.exchange_rate) if self.exchange_rate else None,
            'invoice_number': self.invoice_number,
            'cae_number': self.cae_number,
            'payment_status': self.payment_status,
            'notes': self.notes,
            'is_deleted': self.is_deleted,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by_user_id': self.created_by_user_id,
            'modified_by_user_id': self.modified_by_user_id
        }
        
        if include_supplier and self.supplier:
            data['supplier'] = {
                'id': self.supplier.id,
                'name': self.supplier.name,
                'tax_id': self.supplier.tax_id
            }
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items.all()]
        
        return data
    
    def calculate_total(self):
        """Calculate total amount from items"""
        total = sum(item.total_price for item in self.items.all())
        return total
    
    def can_delete(self):
        """Check if purchase can be deleted (within 7 days)"""
        if not self.created_at:
            return False
        days_since_creation = (datetime.utcnow() - self.created_at).days
        return days_since_creation <= 7
    
    def __repr__(self):
        return f'<Purchase #{self.id} - {self.supplier.name if self.supplier else "Unknown"} - {self.purchase_date}>'
