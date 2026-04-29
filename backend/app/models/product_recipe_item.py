from app.extensions import db

class ProductRecipeItem(db.Model):
    __tablename__ = 'product_recipe_items'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    supply_id = db.Column(db.Integer, db.ForeignKey('supplies.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 4), nullable=False)
    unit = db.Column(db.String(50), nullable=False)

    supply = db.relationship('Supply', backref='recipe_uses')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'supply_id': self.supply_id,
            'supply_name': self.supply.name if self.supply else None,
            'supply_unit': self.supply.unit if self.supply else None,
            'quantity': float(self.quantity),
            'unit': self.unit,
        }
