"""add cancel reasons catalog and cancel_reason_id on POS sales, items and payments

Revision ID: b1b1_add_pos_cash_ui_support
Revises: b1a4_add_pos_sales_engine
Create Date: 2026-10-10 00:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = 'b1b1_add_pos_cash_ui_support'
down_revision = 'b1a4_add_pos_sales_engine'
branch_labels = None
depends_on = None

CANCELLABLE_TABLES = ('pos_sales', 'pos_sale_items', 'pos_payments')
INITIAL_REASONS = ('Error de carga', 'Cliente se arrepintió', 'Invitación de la casa', 'Producto agotado')


def upgrade():
    reasons = op.create_table(
        'cancel_reasons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    for table in CANCELLABLE_TABLES:
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column('cancel_reason_id', sa.Integer(), nullable=True))
            batch.create_foreign_key(f'fk_{table}_cancel_reason_id', 'cancel_reasons', ['cancel_reason_id'], ['id'])
    now = datetime.utcnow()
    op.bulk_insert(reasons, [
        {'name': name, 'position': position, 'is_active': True, 'created_at': now, 'updated_at': now}
        for position, name in enumerate(INITIAL_REASONS)
    ])


def downgrade():
    for table in CANCELLABLE_TABLES:
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint(f'fk_{table}_cancel_reason_id', type_='foreignkey')
            batch.drop_column('cancel_reason_id')
    op.drop_table('cancel_reasons')
