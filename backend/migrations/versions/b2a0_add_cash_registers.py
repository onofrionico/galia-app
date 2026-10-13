"""add cash registers, sessions, movements, counts and events; cash session on POS payments

Revision ID: b2a0_add_cash_registers
Revises: b1b1_add_pos_cash_ui_support
Create Date: 2026-10-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b2a0_add_cash_registers'
down_revision = 'b1b1_add_pos_cash_ui_support'
branch_labels = None
depends_on = None

OPEN_ONLY = "status = 'open'"


def upgrade():
    registers = op.create_table(
        'cash_registers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=60), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'cash_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('register_id', sa.Integer(), sa.ForeignKey('cash_registers.id'), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('opened_at', sa.DateTime(), nullable=False),
        sa.Column('opened_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('opening_float', sa.Numeric(12, 2), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('closing_note', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cash_sessions_register_id', 'cash_sessions', ['register_id'])
    op.create_index('uq_cash_sessions_open_register', 'cash_sessions', ['register_id'], unique=True,
                    postgresql_where=sa.text(OPEN_ONLY), sqlite_where=sa.text(OPEN_ONLY))
    op.create_table(
        'cash_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('cash_sessions.id'), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('expense_id', sa.Integer(), sa.ForeignKey('expenses.id'), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('cancelled_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancel_reason', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cash_movements_session_id', 'cash_movements', ['session_id'])
    op.create_table(
        'cash_session_counts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('cash_sessions.id'), nullable=False),
        sa.Column('payment_method_id', sa.Integer(), sa.ForeignKey('payment_methods.id'), nullable=False),
        sa.Column('method_name', sa.String(length=50), nullable=False),
        sa.Column('expected', sa.Numeric(12, 2), nullable=False),
        sa.Column('counted', sa.Numeric(12, 2), nullable=False),
        sa.Column('difference', sa.Numeric(12, 2), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'payment_method_id', name='uq_cash_session_counts_method'),
    )
    op.create_table(
        'cash_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('register_id', sa.Integer(), sa.ForeignKey('cash_registers.id'), nullable=False),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('cash_sessions.id'), nullable=True),
        sa.Column('kind', sa.String(length=30), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cash_events_session_id', 'cash_events', ['session_id'])
    with op.batch_alter_table('pos_payments') as batch:
        batch.add_column(sa.Column('cash_session_id', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('cancel_cash_session_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_pos_payments_cash_session_id', 'cash_sessions', ['cash_session_id'], ['id'])
        batch.create_foreign_key('fk_pos_payments_cancel_cash_session_id', 'cash_sessions',
                                 ['cancel_cash_session_id'], ['id'])
        batch.create_index('ix_pos_payments_cash_session_id', ['cash_session_id'])
        batch.create_index('ix_pos_payments_cancel_cash_session_id', ['cancel_cash_session_id'])
    op.bulk_insert(registers, [{'name': 'Caja principal', 'position': 0, 'is_active': True}])


def downgrade():
    with op.batch_alter_table('pos_payments') as batch:
        batch.drop_index('ix_pos_payments_cancel_cash_session_id')
        batch.drop_index('ix_pos_payments_cash_session_id')
        batch.drop_constraint('fk_pos_payments_cancel_cash_session_id', type_='foreignkey')
        batch.drop_constraint('fk_pos_payments_cash_session_id', type_='foreignkey')
        batch.drop_column('cancel_cash_session_id')
        batch.drop_column('cash_session_id')
    op.drop_index('ix_cash_events_session_id', table_name='cash_events')
    op.drop_table('cash_events')
    op.drop_table('cash_session_counts')
    op.drop_index('ix_cash_movements_session_id', table_name='cash_movements')
    op.drop_table('cash_movements')
    op.drop_index('uq_cash_sessions_open_register', table_name='cash_sessions')
    op.drop_index('ix_cash_sessions_register_id', table_name='cash_sessions')
    op.drop_table('cash_sessions')
    op.drop_table('cash_registers')
