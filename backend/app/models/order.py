from datetime import datetime
from app.extensions import db


class Order(db.Model):
    """
    Order/Comanda model that accumulates items before becoming a Sale.
    Represents a persistent order with optional mesa and salon associations.
    """
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesas.id'), nullable=True)
    salon_id = db.Column(db.Integer, db.ForeignKey('salones.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='abierta')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    closed_at = db.Column(db.DateTime, nullable=True)
    closed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    mesa = db.relationship('Mesa', backref='orders')
    closed_by_user = db.relationship('User', foreign_keys=[closed_by])

    def total(self):
        """Calculate total of all items in the order"""
        return sum(float(item.unit_price) * item.quantity for item in self.items.all())

    def to_dict(self, include_items=False):
        """
        Convert order to dictionary representation.

        Args:
            include_items: If True, includes order items in the response

        Returns:
            Dictionary with order data
        """
        data = {
            'id': self.id,
            'mesa_id': self.mesa_id,
            'salon_id': self.salon_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'closed_by': self.closed_by,
            'total': self.total()
        }

        if include_items:
            data['items'] = [item.to_dict() for item in self.items.all()]

        return data


class OrderItem(db.Model):
    """
    Individual item in an Order/Comanda.
    Links a product variant to an order with quantity and pricing information.
    """
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text, nullable=True)

    variant = db.relationship('ProductVariant', backref='order_items')

    def to_dict(self):
        """
        Convert order item to dictionary representation.

        Returns:
            Dictionary with item data including product name and subtotal
        """
        product = self.variant.product if self.variant else None
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_variant_id': self.product_variant_id,
            'product_name': product.name if product else None,
            'variant_name': self.variant.name if self.variant else None,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'subtotal': float(self.unit_price) * self.quantity,
            'notes': self.notes
        }
