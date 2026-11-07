from datetime import datetime
from app.extensions import db


class Recipe(db.Model):
    """Receta de producción: una tanda que rinde `yield_quantity` `yield_unit`."""
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True, unique=True)
    yield_quantity = db.Column(db.Numeric(10, 3), nullable=True)
    yield_unit = db.Column(db.String(30), nullable=True)
    total_time_minutes = db.Column(db.Integer, nullable=True)
    advance_notes = db.Column(db.Text, nullable=True)   # ej. "1 día de freezer antes de hornear"
    notes = db.Column(db.Text, nullable=True)
    pending_notes = db.Column(db.Text, nullable=True)   # "a completar", visible como aviso
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    product = db.relationship('Product', backref=db.backref('recipe', uselist=False))
    ingredients = db.relationship('RecipeIngredient', backref='recipe', cascade='all, delete-orphan',
                                  order_by='RecipeIngredient.position',
                                  foreign_keys='RecipeIngredient.recipe_id')
    steps = db.relationship('RecipeStep', backref='recipe', cascade='all, delete-orphan',
                            order_by='RecipeStep.position')


class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'
    __table_args__ = (
        db.CheckConstraint('(supply_id IS NOT NULL AND sub_recipe_id IS NULL) OR '
                           '(supply_id IS NULL AND sub_recipe_id IS NOT NULL)',
                           name='ck_recipe_ingredient_one_source'),
    )

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    supply_id = db.Column(db.Integer, db.ForeignKey('supplies.id'), nullable=True, index=True)
    sub_recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=True, index=True)
    quantity = db.Column(db.Numeric(12, 4), nullable=True)  # null = a completar / a ojo
    unit = db.Column(db.String(30), nullable=True)
    note = db.Column(db.String(200), nullable=True)         # "pizca", "a ojo"

    supply = db.relationship('Supply')
    sub_recipe = db.relationship('Recipe', foreign_keys=[sub_recipe_id])


class RecipeStep(db.Model):
    __tablename__ = 'recipe_steps'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    title = db.Column(db.String(120), nullable=False)
    instruction = db.Column(db.Text, nullable=True)
    temperature_c = db.Column(db.Integer, nullable=True)
    time_min = db.Column(db.Integer, nullable=True)
    time_max = db.Column(db.Integer, nullable=True)
    doneness = db.Column(db.Text, nullable=True)
    tip = db.Column(db.Text, nullable=True)
