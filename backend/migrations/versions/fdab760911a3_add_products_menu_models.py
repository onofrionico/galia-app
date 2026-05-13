"""Add products menu models (ProductCategory, Product, ProductVariant, ProductRecipeItem, SaleItem, Salon, Mesa) and extend Sale/Supply

Revision ID: fdab760911a3
Revises: 4e00a6d26fe1
Create Date: 2026-04-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fdab760911a3'
down_revision = '4e00a6d26fe1'
branch_labels = None
depends_on = None


def upgrade():
    # Create salones (salons/dining areas) table
    op.create_table(
        'salones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create mesas (tables) table
    op.create_table(
        'mesas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('salon_id', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('pos_x', sa.Float(), nullable=False),
        sa.Column('pos_y', sa.Float(), nullable=False),
        sa.Column('width', sa.Float(), nullable=False),
        sa.Column('height', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['salon_id'], ['salones.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_mesas_salon_id'), 'mesas', ['salon_id'], unique=False)

    # Create product_categories table
    op.create_table(
        'product_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('icon', sa.String(length=10), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('has_recipe', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['category_id'], ['product_categories.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)

    # Create product_variants table
    op.create_table(
        'product_variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('stock_quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('min_stock', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_product_variants_product_id'), 'product_variants', ['product_id'], unique=False)

    # Create product_recipe_items table
    op.create_table(
        'product_recipe_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('supply_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['supply_id'], ['supplies.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_product_recipe_items_product_id'), 'product_recipe_items', ['product_id'], unique=False)
    op.create_index(op.f('ix_product_recipe_items_supply_id'), 'product_recipe_items', ['supply_id'], unique=False)

    # Create sale_items table
    op.create_table(
        'sale_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('product_variant_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['product_variant_id'], ['product_variants.id'], ),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sale_items_product_variant_id'), 'sale_items', ['product_variant_id'], unique=False)
    op.create_index(op.f('ix_sale_items_sale_id'), 'sale_items', ['sale_id'], unique=False)

    # Add columns to sales table
    op.add_column('sales', sa.Column('source', sa.String(length=20), nullable=False, server_default='fudo'))
    op.add_column('sales', sa.Column('mesa_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_sales_mesa_id'), 'sales', ['mesa_id'], unique=False)
    op.create_foreign_key('fk_sales_mesa_id_mesas', 'sales', 'mesas', ['mesa_id'], ['id'])

    # Add columns to supplies table
    op.add_column('supplies', sa.Column('stock_quantity', sa.Numeric(precision=10, scale=3), nullable=False, server_default='0'))
    op.add_column('supplies', sa.Column('min_stock', sa.Numeric(precision=10, scale=3), nullable=False, server_default='0'))


def downgrade():
    # Drop columns from supplies table
    op.drop_column('supplies', 'min_stock')
    op.drop_column('supplies', 'stock_quantity')

    # Drop foreign key and index from sales table
    op.drop_constraint('fk_sales_mesa_id_mesas', 'sales', type_='foreignkey')
    op.drop_index(op.f('ix_sales_mesa_id'), table_name='sales')
    op.drop_column('sales', 'mesa_id')
    op.drop_column('sales', 'source')

    # Drop sale_items table
    op.drop_index(op.f('ix_sale_items_sale_id'), table_name='sale_items')
    op.drop_index(op.f('ix_sale_items_product_variant_id'), table_name='sale_items')
    op.drop_table('sale_items')

    # Drop product_recipe_items table
    op.drop_index(op.f('ix_product_recipe_items_supply_id'), table_name='product_recipe_items')
    op.drop_index(op.f('ix_product_recipe_items_product_id'), table_name='product_recipe_items')
    op.drop_table('product_recipe_items')

    # Drop product_variants table
    op.drop_index(op.f('ix_product_variants_product_id'), table_name='product_variants')
    op.drop_table('product_variants')

    # Drop products table
    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_table('products')

    # Drop product_categories table
    op.drop_table('product_categories')

    # Drop mesas table
    op.drop_index(op.f('ix_mesas_salon_id'), table_name='mesas')
    op.drop_table('mesas')

    # Drop salones table
    op.drop_table('salones')
