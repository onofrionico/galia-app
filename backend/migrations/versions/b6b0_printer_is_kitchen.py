"""add is_kitchen to printers

Revision ID: b6b0_printer_is_kitchen
Revises: b6a0_fudo_cutover
Create Date: 2026-10-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b6b0_printer_is_kitchen'
down_revision = 'b6a0_fudo_cutover'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('printers', sa.Column('is_kitchen', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_column('printers', 'is_kitchen')
