"""Add FUdo integration tables

Revision ID: add_fudo_integration
Revises: add_reports_module
Create Date: 2026-02-17 01:36:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_fudo_integration'
down_revision = 'add_reports_module'

def upgrade():
    op.create_table('fudo_sync_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sync_type', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('records_processed', sa.Integer(), nullable=True),
    sa.Column('records_created', sa.Integer(), nullable=True),
    sa.Column('records_updated', sa.Integer(), nullable=True),
    sa.Column('records_failed', sa.Integer(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('sync_metadata', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('fudo_orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fudo_order_id', sa.String(length=100), nullable=False),
    sa.Column('sale_id', sa.Integer(), nullable=True),
    sa.Column('order_data', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('event_type', sa.String(length=50), nullable=True),
    sa.Column('synced_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('fudo_order_id')
    )
    op.create_index(op.f('ix_fudo_orders_fudo_order_id'), 'fudo_orders', ['fudo_order_id'], unique=True)
    
    op.create_table('fudo_expenses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fudo_expense_id', sa.String(length=100), nullable=False),
    sa.Column('expense_id', sa.Integer(), nullable=True),
    sa.Column('expense_data', sa.JSON(), nullable=False),
    sa.Column('synced_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['expense_id'], ['expenses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('fudo_expense_id')
    )
    op.create_index(op.f('ix_fudo_expenses_fudo_expense_id'), 'fudo_expenses', ['fudo_expense_id'], unique=True)
    
    op.create_table('fudo_cash_movements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fudo_movement_id', sa.String(length=100), nullable=False),
    sa.Column('movement_type', sa.String(length=50), nullable=False),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('cash_register', sa.String(length=100), nullable=True),
    sa.Column('payment_method', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('movement_date', sa.DateTime(), nullable=False),
    sa.Column('movement_data', sa.JSON(), nullable=False),
    sa.Column('synced_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('fudo_movement_id')
    )
    op.create_index(op.f('ix_fudo_cash_movements_fudo_movement_id'), 'fudo_cash_movements', ['fudo_movement_id'], unique=True)
    op.create_index('idx_fudo_cash_movements_date', 'fudo_cash_movements', ['movement_date'], unique=False)
    op.create_index('idx_fudo_cash_movements_type', 'fudo_cash_movements', ['movement_type'], unique=False)

def downgrade():
    op.drop_index('idx_fudo_cash_movements_type', table_name='fudo_cash_movements')
    op.drop_index('idx_fudo_cash_movements_date', table_name='fudo_cash_movements')
    op.drop_index(op.f('ix_fudo_cash_movements_fudo_movement_id'), table_name='fudo_cash_movements')
    op.drop_table('fudo_cash_movements')
    
    op.drop_index(op.f('ix_fudo_expenses_fudo_expense_id'), table_name='fudo_expenses')
    op.drop_table('fudo_expenses')
    
    op.drop_index(op.f('ix_fudo_orders_fudo_order_id'), table_name='fudo_orders')
    op.drop_table('fudo_orders')
    
    op.drop_table('fudo_sync_logs')
