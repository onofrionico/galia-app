from app.extensions import db

class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)

    variant = db.relationship('ProductVariant', backref='sale_items')

    def to_dict(self):
        product = self.variant.product if self.variant else None
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'product_variant_id': self.product_variant_id,
            'product_name': product.name if product else None,
            'variant_name': self.variant.name if self.variant else None,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'subtotal': float(self.subtotal),
        }
