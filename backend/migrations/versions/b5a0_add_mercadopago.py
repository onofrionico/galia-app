"""add MercadoPago settings, Point orders, movements, reconciliations; payment flags; Conciliar module

Revision ID: b5a0_add_mercadopago
Revises: b4a0_add_fiscal_invoicing
Create Date: 2026-10-15 12:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = 'b5a0_add_mercadopago'
down_revision = 'b4a0_add_fiscal_invoicing'
branch_labels = None
depends_on = None

ACTIVE = "status IN ('creating', 'created', 'processing', 'canceling')"


def upgrade():
    op.create_table(
        'mp_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('environment', sa.String(length=12), nullable=False, server_default='test'),
        sa.Column('test_access_token', sa.Text(), nullable=True),
        sa.Column('prod_access_token', sa.Text(), nullable=True),
        sa.Column('terminal_id', sa.String(length=80), nullable=True),
        sa.Column('webhook_secret', sa.Text(), nullable=True),
        sa.Column('point_payment_method_id', sa.Integer(), sa.ForeignKey('payment_methods.id'), nullable=True),
        sa.Column('user_id', sa.String(length=30), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('payment_methods') as batch:
        batch.add_column(sa.Column('is_mercadopago', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute("UPDATE payment_methods SET is_mercadopago = true WHERE lower(name) LIKE '%mercado%'")
    with op.batch_alter_table('pos_payments') as batch:
        batch.add_column(sa.Column('mp_payment_id', sa.String(length=80), nullable=True))
    op.create_index('ix_pos_payments_mp_payment_id', 'pos_payments', ['mp_payment_id'])
    op.create_table(
        'mp_point_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), sa.ForeignKey('pos_sales.id'), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('terminal_id', sa.String(length=80), nullable=False),
        sa.Column('mp_order_id', sa.String(length=80), nullable=True),
        sa.Column('external_reference', sa.String(length=64), nullable=False),
        sa.Column('idempotency_key', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=12), nullable=False),
        sa.Column('status_detail', sa.String(length=80), nullable=True),
        sa.Column('error', sa.String(length=255), nullable=True),
        sa.Column('mp_payment_id', sa.String(length=80), nullable=True),
        sa.Column('approved_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('payment_id', sa.Integer(), sa.ForeignKey('pos_payments.id'), nullable=True),
        sa.Column('refunded_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_checked_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('mp_order_id'),
        sa.UniqueConstraint('external_reference'),
        sa.UniqueConstraint('idempotency_key'),
    )
    op.create_index('ix_mp_point_orders_sale_id', 'mp_point_orders', ['sale_id'])
    op.create_index('uq_mp_point_orders_active_terminal', 'mp_point_orders', ['terminal_id'], unique=True,
                    postgresql_where=sa.text(ACTIVE), sqlite_where=sa.text(ACTIVE))
    op.create_table(
        'mp_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mp_payment_id', sa.String(length=80), nullable=False),
        sa.Column('date_created', sa.DateTime(), nullable=False),
        sa.Column('business_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('refunded_amount', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('net_amount', sa.Numeric(14, 2), nullable=True),
        sa.Column('currency', sa.String(length=5), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('status_detail', sa.String(length=80), nullable=True),
        sa.Column('channel', sa.String(length=12), nullable=False),
        sa.Column('payment_type', sa.String(length=30), nullable=True),
        sa.Column('payment_method', sa.String(length=30), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('external_reference', sa.String(length=64), nullable=True),
        sa.Column('payer_label', sa.String(length=120), nullable=True),
        sa.Column('raw', sa.JSON(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('mp_payment_id'),
    )
    op.create_index('ix_mp_movements_business_date', 'mp_movements', ['business_date'])
    op.create_index('ix_mp_movements_external_reference', 'mp_movements', ['external_reference'])
    op.create_table(
        'mp_fetch_days',
        sa.Column('business_date', sa.Date(), nullable=False),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.Column('fetched_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('truncated', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint('business_date'),
    )
    op.create_table(
        'mp_reconciliations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mp_movement_id', sa.Integer(), sa.ForeignKey('mp_movements.id'), nullable=True),
        sa.Column('payment_id', sa.Integer(), sa.ForeignKey('pos_payments.id'), nullable=True),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('uq_mp_reconciliations_movement', 'mp_reconciliations', ['mp_movement_id'], unique=True,
                    postgresql_where=sa.text('mp_movement_id IS NOT NULL'),
                    sqlite_where=sa.text('mp_movement_id IS NOT NULL'))
    op.create_index('uq_mp_reconciliations_payment', 'mp_reconciliations', ['payment_id'], unique=True,
                    postgresql_where=sa.text('payment_id IS NOT NULL'), sqlite_where=sa.text('payment_id IS NOT NULL'))
    now = datetime.utcnow()
    bind = op.get_bind()
    exists = bind.execute(sa.text("SELECT id FROM modules WHERE name = 'Conciliar'")).first()
    if exists is None:
        modules = sa.table('modules', sa.column('name', sa.String), sa.column('display_name', sa.String),
                           sa.column('description', sa.Text), sa.column('icon', sa.String),
                           sa.column('category', sa.String), sa.column('route', sa.String),
                           sa.column('is_active', sa.Boolean), sa.column('created_at', sa.DateTime),
                           sa.column('updated_at', sa.DateTime))
        op.bulk_insert(modules, [{'name': 'Conciliar', 'display_name': 'Conciliar MercadoPago',
                                  'description': 'Traer movimientos de MercadoPago y resolver diferencias',
                                  'icon': None, 'category': 'Operations', 'route': '/mp/reconciliation',
                                  'is_active': True, 'created_at': now, 'updated_at': now}])
        module_id = bind.execute(sa.text("SELECT id FROM modules WHERE name = 'Conciliar'")).scalar()
        role_permissions = sa.table('role_permissions', sa.column('role', sa.String),
                                    sa.column('module_id', sa.Integer), sa.column('is_granted', sa.Boolean),
                                    sa.column('created_at', sa.DateTime), sa.column('updated_at', sa.DateTime))
        op.bulk_insert(role_permissions, [
            {'role': 'admin', 'module_id': module_id, 'is_granted': True, 'created_at': now, 'updated_at': now},
            {'role': 'employee', 'module_id': module_id, 'is_granted': False, 'created_at': now, 'updated_at': now},
        ])


def downgrade():
    bind = op.get_bind()
    module_id = bind.execute(sa.text("SELECT id FROM modules WHERE name = 'Conciliar'")).scalar()
    if module_id is not None:
        bind.execute(sa.text('DELETE FROM user_permissions WHERE module_id = :id'), {'id': module_id})
        bind.execute(sa.text('DELETE FROM role_permissions WHERE module_id = :id'), {'id': module_id})
        bind.execute(sa.text('DELETE FROM modules WHERE id = :id'), {'id': module_id})
    op.drop_index('uq_mp_reconciliations_payment', table_name='mp_reconciliations')
    op.drop_index('uq_mp_reconciliations_movement', table_name='mp_reconciliations')
    op.drop_table('mp_reconciliations')
    op.drop_table('mp_fetch_days')
    op.drop_index('ix_mp_movements_external_reference', table_name='mp_movements')
    op.drop_index('ix_mp_movements_business_date', table_name='mp_movements')
    op.drop_table('mp_movements')
    op.drop_index('uq_mp_point_orders_active_terminal', table_name='mp_point_orders')
    op.drop_index('ix_mp_point_orders_sale_id', table_name='mp_point_orders')
    op.drop_table('mp_point_orders')
    op.drop_index('ix_pos_payments_mp_payment_id', table_name='pos_payments')
    with op.batch_alter_table('pos_payments') as batch:
        batch.drop_column('mp_payment_id')
    with op.batch_alter_table('payment_methods') as batch:
        batch.drop_column('is_mercadopago')
    op.drop_table('mp_settings')
