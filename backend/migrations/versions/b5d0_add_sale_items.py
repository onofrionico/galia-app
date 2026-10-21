"""add sale_items (ítems vendidos de Fudo y del POS, para el reporte por producto)

Revision ID: b5d0_add_sale_items
Revises: b5c0_sales_business_date
Create Date: 2026-10-20 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b5d0_add_sale_items'
down_revision = 'b5c0_sales_business_date'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'sale_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=20), nullable=True),
        sa.Column('product_variant_id', sa.Integer(), nullable=True),
        sa.Column('product_name', sa.String(length=200), nullable=False),
        sa.Column('variant_name', sa.String(length=100), nullable=True),
        sa.Column('category_name', sa.String(length=100), nullable=True),
        sa.Column('quantity', sa.Numeric(10, 3), nullable=False),
        sa.Column('unit_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('total', sa.Numeric(12, 2), nullable=False),
        sa.Column('unit_cost', sa.Numeric(12, 2), nullable=True),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_variant_id'], ['product_variants.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id'),
    )
    op.create_index('ix_sale_items_sale_id', 'sale_items', ['sale_id'])
    op.create_index('ix_sale_items_product_variant_id', 'sale_items', ['product_variant_id'])


def downgrade():
    op.drop_index('ix_sale_items_product_variant_id', table_name='sale_items')
    op.drop_index('ix_sale_items_sale_id', table_name='sale_items')
    op.drop_table('sale_items')
