"""add product catalog tables and supply stock columns

Revision ID: b1a2_add_products_and_supplies
Revises: b1a1_add_suppliers
Create Date: 2026-10-08 00:00:02.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b1a2_add_products_and_supplies'
down_revision = 'b1a1_add_suppliers'
branch_labels = None
depends_on = None


def _timestamps():
    return [
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    ]


def upgrade():
    op.create_table(
        'product_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('icon', sa.String(length=10), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('has_recipe', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('track_stock', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        sa.ForeignKeyConstraint(['category_id'], ['product_categories.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)
    op.create_table(
        'product_variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('stock_quantity', sa.Numeric(precision=10, scale=3), nullable=False, server_default='0'),
        sa.Column('min_stock', sa.Numeric(precision=10, scale=3), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_product_variants_product_id'), 'product_variants', ['product_id'], unique=False)
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

    with op.batch_alter_table('supplies') as batch:
        batch.add_column(sa.Column('stock_quantity', sa.Numeric(precision=10, scale=3), nullable=False, server_default='0'))
        batch.add_column(sa.Column('min_stock', sa.Numeric(precision=10, scale=3), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('supplies') as batch:
        batch.drop_column('min_stock')
        batch.drop_column('stock_quantity')
    op.drop_index(op.f('ix_product_recipe_items_supply_id'), table_name='product_recipe_items')
    op.drop_index(op.f('ix_product_recipe_items_product_id'), table_name='product_recipe_items')
    op.drop_table('product_recipe_items')
    op.drop_index(op.f('ix_product_variants_product_id'), table_name='product_variants')
    op.drop_table('product_variants')
    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_table('products')
    op.drop_table('product_categories')
