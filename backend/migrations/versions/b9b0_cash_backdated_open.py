"""Caja: registered_at para aperturas cargadas con hora anterior

Revision ID: b9b0_cash_backdated_open
Revises: b9a0_vouchers
Create Date: 2026-11-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b9b0_cash_backdated_open'
down_revision = 'b9a0_vouchers'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('cash_sessions', sa.Column('registered_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('cash_sessions') as batch_op:
        batch_op.drop_column('registered_at')
