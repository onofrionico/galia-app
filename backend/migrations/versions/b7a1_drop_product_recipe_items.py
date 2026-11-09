"""drop legacy product_recipe_items (replaced by recipes)

Revision ID: b7a1_drop_product_recipe_items
Revises: b7a0_add_recipes
Create Date: 2026-11-07 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b7a1_drop_product_recipe_items'
down_revision = 'b7a0_add_recipes'
branch_labels = None
depends_on = None


def restore_compositions(bind):
    """Repuebla product_recipe_items desde las recetas vinculadas con rinde 1.

    Solo se vuelcan ingredientes de insumo con cantidad, convertidos a la unidad del
    insumo; el resto (sub-recetas, a completar, otros rindes) no tiene equivalente en el
    modelo viejo y se pierde en el downgrade.
    """
    from decimal import Decimal
    from app.services.units import convert

    legacy = sa.table('product_recipe_items', sa.column('product_id', sa.Integer),
                      sa.column('supply_id', sa.Integer), sa.column('quantity', sa.Numeric),
                      sa.column('unit', sa.String))
    rows = bind.execute(sa.text(
        'SELECT r.product_id, i.supply_id, i.quantity, i.unit, s.unit '
        'FROM recipes r JOIN recipe_ingredients i ON i.recipe_id = r.id '
        'JOIN supplies s ON s.id = i.supply_id '
        'WHERE r.product_id IS NOT NULL AND r.yield_quantity = 1 '
        'AND i.supply_id IS NOT NULL AND i.quantity IS NOT NULL '
        'ORDER BY r.product_id, i.position, i.id')).fetchall()
    for product_id, supply_id, quantity, unit, supply_unit in rows:
        converted = convert(Decimal(str(quantity)), unit, supply_unit)
        if converted is None or converted <= 0:
            continue
        bind.execute(sa.insert(legacy).values(
            product_id=product_id, supply_id=supply_id, quantity=converted, unit=supply_unit))


def upgrade():
    op.drop_index(op.f('ix_product_recipe_items_supply_id'), table_name='product_recipe_items')
    op.drop_index(op.f('ix_product_recipe_items_product_id'), table_name='product_recipe_items')
    op.drop_table('product_recipe_items')


def downgrade():
    op.create_table(
        'product_recipe_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('supply_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['supply_id'], ['supplies.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_product_recipe_items_product_id'), 'product_recipe_items', ['product_id'], unique=False)
    op.create_index(op.f('ix_product_recipe_items_supply_id'), 'product_recipe_items', ['supply_id'], unique=False)
    restore_compositions(op.get_bind())
