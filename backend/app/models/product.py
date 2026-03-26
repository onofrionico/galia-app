from datetime import datetime
from app.extensions import db

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    product_master_id = db.Column(db.Integer, db.ForeignKey('product_masters.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    unit_of_measure = db.Column(db.String(50), nullable=False)
    current_price = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    modified_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    supplier = db.relationship('Supplier', back_populates='products')
    product_master = db.relationship('ProductMaster', back_populates='products')
    purchase_items = db.relationship('PurchaseItem', back_populates='product', lazy='dynamic')
    price_history = db.relationship('PriceHistory', back_populates='product', lazy='dynamic', order_by='PriceHistory.effective_date.desc()')
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])
    modified_by = db.relationship('User', foreign_keys=[modified_by_user_id])
    
    __table_args__ = (
        db.UniqueConstraint('supplier_id', 'sku', name='uq_supplier_sku'),
        db.Index('idx_products_supplier_id', 'supplier_id'),
        db.Index('idx_products_product_master_id', 'product_master_id'),
        db.Index('idx_products_name', 'name'),
        db.Index('idx_products_sku', 'sku'),
        db.Index('idx_products_status', 'status'),
        db.Index('idx_products_is_deleted', 'is_deleted'),
    )
    
    def to_dict(self, include_supplier=False, include_price_history=False):
        data = {
            'id': self.id,
            'supplier_id': self.supplier_id,
            'product_master_id': self.product_master_id,
            'name': self.name,
            'sku': self.sku,
            'category': self.category,
            'unit_of_measure': self.unit_of_measure,
            'current_price': float(self.current_price) if self.current_price else 0,
            'status': self.status,
            'is_deleted': self.is_deleted,
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
        
        if include_price_history:
            data['price_history'] = [ph.to_dict() for ph in self.price_history.limit(10).all()]
        
        if self.product_master:
            data['product_master'] = {
                'id': self.product_master.id,
                'name': self.product_master.name
            }
        
        return data
    
    def __repr__(self):
        return f'<Product {self.name} ({self.sku})>'
