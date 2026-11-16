"""Vouchers de descuento: tandas, vouchers, historial, enlace con descuentos del POS y módulo

Revision ID: b9a0_vouchers
Revises: b7c0_production_forecast
Create Date: 2026-11-16 12:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = 'b9a0_vouchers'
down_revision = 'b7c0_production_forecast'
branch_labels = None
depends_on = None

MODULE = ('Vouchers', 'Vouchers', 'Tandas de vouchers de descuento', '/vouchers')
ACTIVE_WHERE = 'cancelled_at IS NULL AND voucher_id IS NOT NULL'


def upgrade():
    op.create_table(
        'voucher_batches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('min_sale_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('expires_at', sa.Date(), nullable=False),
        sa.Column('terms', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        'vouchers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('batch_id', sa.Integer(), sa.ForeignKey('voucher_batches.id'), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('voided_at', sa.DateTime(), nullable=True),
        sa.Column('voided_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('void_reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_vouchers_batch_id', 'vouchers', ['batch_id'])
    op.create_index('ix_vouchers_code', 'vouchers', ['code'], unique=True)
    op.create_table(
        'voucher_change_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('batch_id', sa.Integer(), sa.ForeignKey('voucher_batches.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('field', sa.String(50), nullable=False),
        sa.Column('old_value', sa.String(100), nullable=True),
        sa.Column('new_value', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_voucher_change_log_batch_id', 'voucher_change_log', ['batch_id'])

    with op.batch_alter_table('pos_discounts') as batch:
        batch.add_column(sa.Column('voucher_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_pos_discounts_voucher_id', 'vouchers', ['voucher_id'], ['id'])
        batch.create_index('ix_pos_discounts_voucher_id', ['voucher_id'])
    op.create_index('uq_pos_discounts_active_voucher', 'pos_discounts', ['voucher_id'], unique=True,
                    postgresql_where=sa.text(ACTIVE_WHERE), sqlite_where=sa.text(ACTIVE_WHERE))

    now = datetime.utcnow()
    name, display, description, route = MODULE
    modules = sa.table('modules', sa.column('name', sa.String), sa.column('display_name', sa.String),
                       sa.column('description', sa.Text), sa.column('icon', sa.String),
                       sa.column('category', sa.String), sa.column('route', sa.String),
                       sa.column('is_active', sa.Boolean), sa.column('created_at', sa.DateTime),
                       sa.column('updated_at', sa.DateTime))
    op.bulk_insert(modules, [{'name': name, 'display_name': display, 'description': description, 'icon': None,
                              'category': 'Operations', 'route': route, 'is_active': True, 'created_at': now,
                              'updated_at': now}])
    module_id = op.get_bind().execute(sa.text('SELECT id FROM modules WHERE name = :n'), {'n': name}).scalar()
    role_permissions = sa.table('role_permissions', sa.column('role', sa.String), sa.column('module_id', sa.Integer),
                                sa.column('is_granted', sa.Boolean), sa.column('created_at', sa.DateTime),
                                sa.column('updated_at', sa.DateTime))
    op.bulk_insert(role_permissions, [
        {'role': 'admin', 'module_id': module_id, 'is_granted': True, 'created_at': now, 'updated_at': now},
        {'role': 'employee', 'module_id': module_id, 'is_granted': False, 'created_at': now, 'updated_at': now},
    ])


def downgrade():
    bind = op.get_bind()
    module_id = bind.execute(sa.text('SELECT id FROM modules WHERE name = :n'), {'n': MODULE[0]}).scalar()
    if module_id is not None:
        bind.execute(sa.text('DELETE FROM user_permissions WHERE module_id = :m'), {'m': module_id})
        bind.execute(sa.text('DELETE FROM role_permissions WHERE module_id = :m'), {'m': module_id})
        bind.execute(sa.text('DELETE FROM modules WHERE id = :m'), {'m': module_id})
    op.drop_index('uq_pos_discounts_active_voucher', table_name='pos_discounts')
    with op.batch_alter_table('pos_discounts') as batch:
        batch.drop_index('ix_pos_discounts_voucher_id')
        batch.drop_constraint('fk_pos_discounts_voucher_id', type_='foreignkey')
        batch.drop_column('voucher_id')
    op.drop_table('voucher_change_log')
    op.drop_table('vouchers')
    op.drop_table('voucher_batches')
