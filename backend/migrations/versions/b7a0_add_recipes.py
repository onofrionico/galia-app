"""add production recipes (recipes, ingredients, steps), variant recipe_units, Recipes modules

Revision ID: b7a0_add_recipes
Revises: b6e0_schedule_is_public
Create Date: 2026-11-07 12:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = 'b7a0_add_recipes'
down_revision = 'b6e0_schedule_is_public'
branch_labels = None
depends_on = None

MODULES = [
    ('Recipes', 'Ver recetas', 'Consultar las recetas de producción'),
    ('RecipeCosts', 'Ver costo de recetas', 'Ver el costo de insumos de las recetas y productos'),
    ('RecipesAdmin', 'Administrar recetas', 'Crear y editar recetas de producción'),
]
PENDING = 'Migrada de la composición anterior: faltan pasos.'


def copy_compositions(bind):
    """Crea una receta por cada producto con composición en product_recipe_items.

    Cantidad idéntica y unidad = unidad del insumo, así la conversión es identidad
    y el descuento de stock no cambia. Idempotente: saltea productos con receta.
    Solo Core (sin ORM), para correr igual en SQLite y PostgreSQL.
    """
    now = datetime.utcnow()
    recipes = sa.table('recipes', sa.column('id', sa.Integer), sa.column('name', sa.String),
                       sa.column('product_id', sa.Integer), sa.column('yield_quantity', sa.Numeric),
                       sa.column('yield_unit', sa.String), sa.column('pending_notes', sa.Text),
                       sa.column('is_active', sa.Boolean), sa.column('created_at', sa.DateTime),
                       sa.column('updated_at', sa.DateTime))
    ingredients = sa.table('recipe_ingredients', sa.column('recipe_id', sa.Integer),
                           sa.column('position', sa.Integer), sa.column('supply_id', sa.Integer),
                           sa.column('quantity', sa.Numeric), sa.column('unit', sa.String))

    product_ids = [row[0] for row in bind.execute(sa.text(
        'SELECT DISTINCT product_id FROM product_recipe_items ORDER BY product_id'))]
    for product_id in product_ids:
        if bind.execute(sa.text('SELECT 1 FROM recipes WHERE product_id = :p'),
                        {'p': product_id}).first() is not None:
            continue
        product_name = bind.execute(sa.text('SELECT name FROM products WHERE id = :p'),
                                    {'p': product_id}).scalar()
        if product_name is None:
            continue
        name = product_name[:150]
        if bind.execute(sa.text('SELECT 1 FROM recipes WHERE name = :n'), {'n': name}).first() is not None:
            name = f'{product_name[:120]} (producto #{product_id})'
        bind.execute(sa.insert(recipes).values(
            name=name, product_id=product_id, yield_quantity=1, yield_unit='unidad',
            pending_notes=PENDING, is_active=True, created_at=now, updated_at=now))
        recipe_id = bind.execute(sa.text('SELECT id FROM recipes WHERE product_id = :p'),
                                 {'p': product_id}).scalar()
        rows = bind.execute(sa.text(
            'SELECT i.supply_id, i.quantity, s.unit FROM product_recipe_items i '
            'JOIN supplies s ON s.id = i.supply_id WHERE i.product_id = :p ORDER BY i.id'),
            {'p': product_id}).fetchall()
        for position, (supply_id, quantity, supply_unit) in enumerate(rows):
            bind.execute(sa.insert(ingredients).values(
                recipe_id=recipe_id, position=position, supply_id=supply_id,
                quantity=quantity, unit=supply_unit))


def upgrade():
    op.create_table(
        'recipes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=True),
        sa.Column('yield_quantity', sa.Numeric(10, 3), nullable=True),
        sa.Column('yield_unit', sa.String(length=50), nullable=True),
        sa.Column('total_time_minutes', sa.Integer(), nullable=True),
        sa.Column('advance_notes', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('pending_notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('product_id'),
    )
    op.create_table(
        'recipe_ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), sa.ForeignKey('recipes.id'), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('supply_id', sa.Integer(), sa.ForeignKey('supplies.id'), nullable=True),
        sa.Column('sub_recipe_id', sa.Integer(), sa.ForeignKey('recipes.id'), nullable=True),
        sa.Column('quantity', sa.Numeric(12, 4), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('note', sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('(supply_id IS NOT NULL AND sub_recipe_id IS NULL) OR '
                           '(supply_id IS NULL AND sub_recipe_id IS NOT NULL)',
                           name='ck_recipe_ingredient_one_source'),
    )
    op.create_index('ix_recipe_ingredients_recipe_id', 'recipe_ingredients', ['recipe_id'])
    op.create_index('ix_recipe_ingredients_supply_id', 'recipe_ingredients', ['supply_id'])
    op.create_index('ix_recipe_ingredients_sub_recipe_id', 'recipe_ingredients', ['sub_recipe_id'])
    op.create_table(
        'recipe_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), sa.ForeignKey('recipes.id'), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('instruction', sa.Text(), nullable=True),
        sa.Column('temperature_c', sa.Integer(), nullable=True),
        sa.Column('time_min', sa.Integer(), nullable=True),
        sa.Column('time_max', sa.Integer(), nullable=True),
        sa.Column('doneness', sa.Text(), nullable=True),
        sa.Column('tip', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_recipe_steps_recipe_id', 'recipe_steps', ['recipe_id'])
    with op.batch_alter_table('product_variants') as batch:
        batch.add_column(sa.Column('recipe_units', sa.Numeric(10, 3), nullable=False, server_default='1'))

    now = datetime.utcnow()
    bind = op.get_bind()
    modules = sa.table('modules', sa.column('name', sa.String), sa.column('display_name', sa.String),
                       sa.column('description', sa.Text), sa.column('icon', sa.String),
                       sa.column('category', sa.String), sa.column('route', sa.String),
                       sa.column('is_active', sa.Boolean), sa.column('created_at', sa.DateTime),
                       sa.column('updated_at', sa.DateTime))
    role_permissions = sa.table('role_permissions', sa.column('role', sa.String),
                                sa.column('module_id', sa.Integer), sa.column('is_granted', sa.Boolean),
                                sa.column('created_at', sa.DateTime), sa.column('updated_at', sa.DateTime))
    for name, display_name, description in MODULES:
        exists = bind.execute(sa.text('SELECT id FROM modules WHERE name = :n'), {'n': name}).first()
        if exists is not None:
            continue
        op.bulk_insert(modules, [{'name': name, 'display_name': display_name, 'description': description,
                                  'icon': None, 'category': 'Operations', 'route': '/recipes',
                                  'is_active': True, 'created_at': now, 'updated_at': now}])
        module_id = bind.execute(sa.text('SELECT id FROM modules WHERE name = :n'), {'n': name}).scalar()
        op.bulk_insert(role_permissions, [
            {'role': 'admin', 'module_id': module_id, 'is_granted': True, 'created_at': now, 'updated_at': now},
            {'role': 'employee', 'module_id': module_id, 'is_granted': False, 'created_at': now, 'updated_at': now},
        ])

    copy_compositions(bind)


def downgrade():
    bind = op.get_bind()
    for name, _display, _description in MODULES:
        module_id = bind.execute(sa.text('SELECT id FROM modules WHERE name = :n'), {'n': name}).scalar()
        if module_id is not None:
            bind.execute(sa.text('DELETE FROM user_permissions WHERE module_id = :id'), {'id': module_id})
            bind.execute(sa.text('DELETE FROM role_permissions WHERE module_id = :id'), {'id': module_id})
            bind.execute(sa.text('DELETE FROM modules WHERE id = :id'), {'id': module_id})
    with op.batch_alter_table('product_variants') as batch:
        batch.drop_column('recipe_units')
    op.drop_index('ix_recipe_steps_recipe_id', table_name='recipe_steps')
    op.drop_table('recipe_steps')
    op.drop_index('ix_recipe_ingredients_sub_recipe_id', table_name='recipe_ingredients')
    op.drop_index('ix_recipe_ingredients_supply_id', table_name='recipe_ingredients')
    op.drop_index('ix_recipe_ingredients_recipe_id', table_name='recipe_ingredients')
    op.drop_table('recipe_ingredients')
    op.drop_table('recipes')
