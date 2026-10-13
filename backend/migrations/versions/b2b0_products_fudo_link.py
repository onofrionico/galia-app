"""link product categories and variants to Fudo

Revision ID: b2b0_products_fudo_link
Revises: b2a0_add_cash_registers
Create Date: 2026-10-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b2b0_products_fudo_link'
down_revision = 'b2a0_add_cash_registers'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('product_categories') as batch:
        batch.add_column(sa.Column('fudo_category_id', sa.String(20), nullable=True))
        batch.add_column(sa.Column('fudo_status', sa.String(20), nullable=True))
        batch.create_unique_constraint('uq_product_categories_fudo_category_id', ['fudo_category_id'])
    with op.batch_alter_table('product_variants') as batch:
        batch.add_column(sa.Column('fudo_product_id', sa.String(20), nullable=True))
        batch.add_column(sa.Column('fudo_status', sa.String(20), nullable=True))
        batch.create_unique_constraint('uq_product_variants_fudo_product_id', ['fudo_product_id'])


def downgrade():
    with op.batch_alter_table('product_variants') as batch:
        batch.drop_constraint('uq_product_variants_fudo_product_id', type_='unique')
        batch.drop_column('fudo_status')
        batch.drop_column('fudo_product_id')
    with op.batch_alter_table('product_categories') as batch:
        batch.drop_constraint('uq_product_categories_fudo_category_id', type_='unique')
        batch.drop_column('fudo_status')
        batch.drop_column('fudo_category_id')
