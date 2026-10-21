from app.extensions import db


class SaleItem(db.Model):
    """Ítem vendido de una fila de `sales`, con la misma forma para ventas de Fudo y del POS.

    Nombre, variante y categoría se guardan como estaban al vender. Solo ítems no cancelados.
    """
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id', ondelete='CASCADE'), nullable=False, index=True)
    external_id = db.Column(db.String(20), unique=True, nullable=True)  # id del ítem en Fudo
    product_variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id', ondelete='SET NULL'),
                                   nullable=True, index=True)
    product_name = db.Column(db.String(200), nullable=False)
    variant_name = db.Column(db.String(100), nullable=True)
    category_name = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    total = db.Column(db.Numeric(12, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=True)

    sale = db.relationship('Sale', back_populates='items')
