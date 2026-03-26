from app.extensions import db

class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_name_snapshot = db.Column(db.String(200), nullable=False)
    sku_snapshot = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Numeric(12, 4), nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    catalog_price_at_time = db.Column(db.Numeric(12, 2), nullable=True)
    total_price = db.Column(db.Numeric(12, 2), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    purchase = db.relationship('Purchase', back_populates='items')
    product = db.relationship('Product', back_populates='purchase_items')
    
    __table_args__ = (
        db.Index('idx_purchase_items_purchase_id', 'purchase_id'),
        db.Index('idx_purchase_items_product_id', 'product_id'),
    )
    
    def to_dict(self, include_product=False):
        data = {
            'id': self.id,
            'purchase_id': self.purchase_id,
            'product_id': self.product_id,
            'product_name_snapshot': self.product_name_snapshot,
            'sku_snapshot': self.sku_snapshot,
            'quantity': float(self.quantity) if self.quantity else 0,
            'unit_price': float(self.unit_price) if self.unit_price else 0,
            'catalog_price_at_time': float(self.catalog_price_at_time) if self.catalog_price_at_time else None,
            'total_price': float(self.total_price) if self.total_price else 0,
            'notes': self.notes
        }
        
        if include_product and self.product:
            data['product'] = {
                'id': self.product.id,
                'name': self.product.name,
                'sku': self.product.sku,
                'current_price': float(self.product.current_price) if self.product.current_price else 0
            }
        
        return data
    
    def has_price_variance(self):
        """Check if purchase price differs from catalog price"""
        if not self.catalog_price_at_time:
            return False
        return abs(float(self.unit_price) - float(self.catalog_price_at_time)) > 0.01
    
    def price_variance_percentage(self):
        """Calculate percentage variance from catalog price"""
        if not self.catalog_price_at_time or self.catalog_price_at_time == 0:
            return None
        variance = ((float(self.unit_price) - float(self.catalog_price_at_time)) / float(self.catalog_price_at_time)) * 100
        return round(variance, 2)
    
    def __repr__(self):
        return f'<PurchaseItem {self.product_name_snapshot} x {self.quantity}>'
