"""Fidelización: clientes, premios, movimientos de cafecitos, configuración, historial y módulo

Revision ID: b8a0_loyalty
Revises: b7a1_drop_product_recipe_items
Create Date: 2026-11-06 12:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = 'b8a0_loyalty'
down_revision = 'b7a1_drop_product_recipe_items'
branch_labels = None
depends_on = None

MODULE = ('Fidelizacion', 'Fidelización', 'Clientes, cafecitos, premios y reportes', '/fidelizacion')


def upgrade():
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('google_sub', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('search_text', sa.String(600), nullable=False, server_default=''),
        sa.Column('qr_token', sa.String(64), nullable=False, unique=True),
        sa.Column('terms_accepted_at', sa.DateTime(), nullable=False),
        sa.Column('promo_opt_in_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_customers_email', 'customers', ['email'])
    op.create_index('ix_customers_phone', 'customers', ['phone'])
    op.create_index('ix_customers_search_text', 'customers', ['search_text'])

    op.create_table(
        'loyalty_rewards',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('product_variant_id', sa.Integer(), sa.ForeignKey('product_variants.id'), nullable=False),
        sa.Column('cost', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.add_column('product_variants', sa.Column('cafecitos', sa.Integer(), nullable=False, server_default='0'))
    with op.batch_alter_table('pos_sales') as batch:
        batch.add_column(sa.Column('customer_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_pos_sales_customer_id', 'customers', ['customer_id'], ['id'])
        batch.create_index('ix_pos_sales_customer_id', ['customer_id'])
    with op.batch_alter_table('pos_sale_items') as batch:
        batch.add_column(sa.Column('reward_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_pos_sale_items_reward_id', 'loyalty_rewards', ['reward_id'], ['id'])

    op.create_table(
        'loyalty_movements',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('pos_sale_id', sa.Integer(), sa.ForeignKey('pos_sales.id'), nullable=True),
        sa.Column('pos_sale_item_id', sa.Integer(), sa.ForeignKey('pos_sale_items.id'), nullable=True),
        sa.Column('reward_id', sa.Integer(), sa.ForeignKey('loyalty_rewards.id'), nullable=True),
        sa.Column('reward_cost', sa.Integer(), nullable=True),
        sa.Column('pesos_value', sa.Numeric(12, 2), nullable=True),
        sa.Column('reversal_of_id', sa.Integer(), sa.ForeignKey('loyalty_movements.id'), nullable=True),
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for column in ('customer_id', 'pos_sale_id', 'pos_sale_item_id', 'reversal_of_id', 'created_at'):
        op.create_index(f'ix_loyalty_movements_{column}', 'loyalty_movements', [column])

    op.create_table(
        'loyalty_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('active_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )

    op.create_table(
        'loyalty_change_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('entity', sa.String(30), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('field', sa.String(50), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_loyalty_change_log_entity', 'loyalty_change_log', ['entity'])
    op.create_index('ix_loyalty_change_log_created_at', 'loyalty_change_log', ['created_at'])

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
    op.drop_table('loyalty_change_log')
    op.drop_table('loyalty_settings')
    op.drop_table('loyalty_movements')
    with op.batch_alter_table('pos_sale_items') as batch:
        batch.drop_constraint('fk_pos_sale_items_reward_id', type_='foreignkey')
        batch.drop_column('reward_id')
    with op.batch_alter_table('pos_sales') as batch:
        batch.drop_index('ix_pos_sales_customer_id')
        batch.drop_constraint('fk_pos_sales_customer_id', type_='foreignkey')
        batch.drop_column('customer_id')
    op.drop_column('product_variants', 'cafecitos')
    op.drop_table('loyalty_rewards')
    op.drop_table('customers')
