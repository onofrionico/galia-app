from datetime import datetime
from app.extensions import db

class PriceHistory(db.Model):
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    change_percentage = db.Column(db.Numeric(8, 2), nullable=True)
    source = db.Column(db.String(50), nullable=False)
    related_purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    product = db.relationship('Product', back_populates='price_history')
    related_purchase = db.relationship('Purchase', back_populates='price_history_entries')
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])
    
    __table_args__ = (
        db.Index('idx_price_history_product_id', 'product_id'),
        db.Index('idx_price_history_effective_date', 'effective_date'),
        db.Index('idx_price_history_source', 'source'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'price': float(self.price) if self.price else 0,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'change_percentage': float(self.change_percentage) if self.change_percentage else None,
            'source': self.source,
            'related_purchase_id': self.related_purchase_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by_user_id': self.created_by_user_id
        }
    
    @staticmethod
    def calculate_change_percentage(old_price, new_price):
        """Calculate percentage change between two prices"""
        if not old_price or old_price == 0:
            return None
        change = ((float(new_price) - float(old_price)) / float(old_price)) * 100
        return round(change, 2)
    
    def __repr__(self):
        return f'<PriceHistory Product#{self.product_id} - {self.price} on {self.effective_date}>'
