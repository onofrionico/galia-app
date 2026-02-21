"""Add external_id column to sales table

Revision ID: add_external_id_to_sales
Revises: add_fudo_integration
Create Date: 2026-02-17 10:16:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_external_id_to_sales'
down_revision = 'add_fudo_integration'

def upgrade():
    op.add_column('sales', sa.Column('external_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_sales_external_id'), 'sales', ['external_id'], unique=True)

def downgrade():
    op.drop_index(op.f('ix_sales_external_id'), table_name='sales')
    op.drop_column('sales', 'external_id')
