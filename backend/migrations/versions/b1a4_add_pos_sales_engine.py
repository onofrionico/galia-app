"""add POS sales engine tables, sales.source, POS modules and payment methods

Revision ID: b1a4_add_pos_sales_engine
Revises: b1a3_add_site_config
Create Date: 2026-10-09 00:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = 'b1a4_add_pos_sales_engine'
down_revision = 'b1a3_add_site_config'
branch_labels = None
depends_on = None

POS_MODULES = [
    ('POS', 'Caja (POS)', 'Plano de mesas, ventas, mostrador, cobro y configuración de salones', '/pos'),
    ('Camarero', 'Camarero', 'Abrir mesas, cargar pedidos y pedir la cuenta', '/camarero'),
    ('Cobrar', 'Cobrar', 'Registrar pagos y cerrar ventas', None),
    ('Anular', 'Anular', 'Anular ítems confirmados, pagos y ventas', None),
    ('Descuentos', 'Descuentos', 'Descuentos libres y plantillas restringidas', None),
]
PAYMENT_METHODS = [
    ('Efectivo', 'cash', 0), ('Débito', 'card', 1), ('Crédito', 'card', 2),
    ('Transferencia', 'transfer', 3), ('MercadoPago', 'other', 4),
]


def _timestamps():
    return [
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    ]


def upgrade():
    op.create_table(
        'salons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'pos_tables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('salon_id', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('pos_x', sa.Float(), nullable=False, server_default='10'),
        sa.Column('pos_y', sa.Float(), nullable=False, server_default='10'),
        sa.Column('width', sa.Float(), nullable=False, server_default='10'),
        sa.Column('height', sa.Float(), nullable=False, server_default='10'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        sa.ForeignKeyConstraint(['salon_id'], ['salons.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('salon_id', 'number', name='uq_pos_tables_salon_number'),
    )
    op.create_index(op.f('ix_pos_tables_salon_id'), 'pos_tables', ['salon_id'])
    op.create_table(
        'modifier_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('min_select', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_select', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'modifier_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('price_delta', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('supply_id', sa.Integer(), nullable=True),
        sa.Column('supply_quantity', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(['group_id'], ['modifier_groups.id']),
        sa.ForeignKeyConstraint(['supply_id'], ['supplies.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_modifier_options_group_id'), 'modifier_options', ['group_id'])
    op.create_table(
        'product_modifier_groups',
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['group_id'], ['modifier_groups.id']),
        sa.PrimaryKeyConstraint('product_id', 'group_id'),
    )
    payment_methods = op.create_table(
        'payment_methods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'discount_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('value', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('scope', sa.String(length=10), nullable=False),
        sa.Column('restricted', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'pos_sales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_date', sa.Date(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('sale_type', sa.String(length=10), nullable=False),
        sa.Column('table_id', sa.Integer(), nullable=True),
        sa.Column('people', sa.Integer(), nullable=True),
        sa.Column('customer_name', sa.String(length=100), nullable=True),
        sa.Column('comment', sa.String(length=500), nullable=True),
        sa.Column('waiter_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=10), nullable=False, server_default='open'),
        sa.Column('opened_at', sa.DateTime(), nullable=False),
        sa.Column('opened_by', sa.Integer(), nullable=False),
        sa.Column('billing_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_by', sa.Integer(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_by', sa.Integer(), nullable=True),
        sa.Column('cancel_reason', sa.String(length=255), nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('discount_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('paid_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('split_from_id', sa.Integer(), nullable=True),
        sa.Column('sale_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['table_id'], ['pos_tables.id']),
        sa.ForeignKeyConstraint(['waiter_id'], ['users.id']),
        sa.ForeignKeyConstraint(['opened_by'], ['users.id']),
        sa.ForeignKeyConstraint(['closed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['cancelled_by'], ['users.id']),
        sa.ForeignKeyConstraint(['split_from_id'], ['pos_sales.id']),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('business_date', 'number', name='uq_pos_sales_day_number'),
    )
    op.create_index(op.f('ix_pos_sales_table_id'), 'pos_sales', ['table_id'])
    op.create_index(op.f('ix_pos_sales_status'), 'pos_sales', ['status'])
    op.create_index(op.f('ix_pos_sales_opened_at'), 'pos_sales', ['opened_at'])
    op.create_table(
        'pos_sale_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('product_variant_id', sa.Integer(), nullable=False),
        sa.Column('product_name', sa.String(length=200), nullable=False),
        sa.Column('variant_name', sa.String(length=100), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('modifiers_total', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('line_total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False, server_default='pending'),
        sa.Column('batch', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('confirmed_by', sa.Integer(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_by', sa.Integer(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancel_reason', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['sale_id'], ['pos_sales.id']),
        sa.ForeignKeyConstraint(['product_variant_id'], ['product_variants.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['confirmed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['cancelled_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pos_sale_items_sale_id'), 'pos_sale_items', ['sale_id'])
    op.create_table(
        'pos_sale_item_modifiers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('option_id', sa.Integer(), nullable=False),
        sa.Column('group_name', sa.String(length=100), nullable=False),
        sa.Column('option_name', sa.String(length=100), nullable=False),
        sa.Column('price_delta', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('supply_id', sa.Integer(), nullable=True),
        sa.Column('supply_quantity', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['pos_sale_items.id']),
        sa.ForeignKeyConstraint(['option_id'], ['modifier_options.id']),
        sa.ForeignKeyConstraint(['supply_id'], ['supplies.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pos_sale_item_modifiers_item_id'), 'pos_sale_item_modifiers', ['item_id'])
    op.create_table(
        'pos_discounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('value', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('cancelled_by', sa.Integer(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['sale_id'], ['pos_sales.id']),
        sa.ForeignKeyConstraint(['item_id'], ['pos_sale_items.id']),
        sa.ForeignKeyConstraint(['template_id'], ['discount_templates.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['cancelled_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pos_discounts_sale_id'), 'pos_discounts', ['sale_id'])
    op.create_index(op.f('ix_pos_discounts_item_id'), 'pos_discounts', ['item_id'])
    op.create_table(
        'pos_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('payment_method_id', sa.Integer(), nullable=False),
        sa.Column('method_name', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('tendered', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('change', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('client_request_id', sa.String(length=64), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('cancelled_by', sa.Integer(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancel_reason', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['sale_id'], ['pos_sales.id']),
        sa.ForeignKeyConstraint(['payment_method_id'], ['payment_methods.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['cancelled_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_request_id'),
    )
    op.create_index(op.f('ix_pos_payments_sale_id'), 'pos_payments', ['sale_id'])
    op.create_table(
        'pos_sale_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=30), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['sale_id'], ['pos_sales.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pos_sale_events_sale_id'), 'pos_sale_events', ['sale_id'])
    op.create_index(op.f('ix_pos_sale_events_created_at'), 'pos_sale_events', ['created_at'])

    with op.batch_alter_table('sales') as batch:
        batch.add_column(sa.Column('source', sa.String(length=20), nullable=False, server_default='fudo'))

    now = datetime.utcnow()
    modules = sa.table('modules', sa.column('name', sa.String), sa.column('display_name', sa.String),
                       sa.column('description', sa.Text), sa.column('icon', sa.String),
                       sa.column('category', sa.String), sa.column('route', sa.String),
                       sa.column('is_active', sa.Boolean), sa.column('created_at', sa.DateTime),
                       sa.column('updated_at', sa.DateTime))
    op.bulk_insert(modules, [
        {'name': name, 'display_name': display, 'description': description, 'icon': None,
         'category': 'Operations', 'route': route, 'is_active': True, 'created_at': now, 'updated_at': now}
        for name, display, description, route in POS_MODULES
    ])
    names = [m[0] for m in POS_MODULES]
    rows = op.get_bind().execute(
        sa.text('SELECT id FROM modules WHERE name IN :names').bindparams(sa.bindparam('names', expanding=True)),
        {'names': names},
    ).fetchall()
    role_permissions = sa.table('role_permissions', sa.column('role', sa.String), sa.column('module_id', sa.Integer),
                                sa.column('is_granted', sa.Boolean), sa.column('created_at', sa.DateTime),
                                sa.column('updated_at', sa.DateTime))
    grants = []
    for (module_id,) in rows:
        grants.append({'role': 'admin', 'module_id': module_id, 'is_granted': True, 'created_at': now, 'updated_at': now})
        grants.append({'role': 'employee', 'module_id': module_id, 'is_granted': False, 'created_at': now,
                       'updated_at': now})
    op.bulk_insert(role_permissions, grants)
    op.bulk_insert(payment_methods, [
        {'name': name, 'kind': kind, 'position': position, 'is_active': True}
        for name, kind, position in PAYMENT_METHODS
    ])


def downgrade():
    """Revierte el motor POS. Elimina las filas de `sales` proyectadas por el POS (source = 'galia')."""
    bind = op.get_bind()
    names_param = sa.bindparam('names', expanding=True)
    names = {'names': [m[0] for m in POS_MODULES]}
    bind.execute(sa.text('DELETE FROM user_permissions WHERE module_id IN '
                         '(SELECT id FROM modules WHERE name IN :names)').bindparams(names_param), names)
    bind.execute(sa.text('DELETE FROM role_permissions WHERE module_id IN '
                         '(SELECT id FROM modules WHERE name IN :names)').bindparams(names_param), names)
    bind.execute(sa.text('DELETE FROM modules WHERE name IN :names').bindparams(names_param), names)

    # Las ventas proyectadas desde el POS pierden su origen: se eliminan junto con pos_sales.
    bind.execute(sa.text("DELETE FROM sales WHERE source = 'galia'"))
    with op.batch_alter_table('sales') as batch:
        batch.drop_column('source')

    for index, table in [
        ('ix_pos_sale_events_created_at', 'pos_sale_events'), ('ix_pos_sale_events_sale_id', 'pos_sale_events'),
        ('ix_pos_payments_sale_id', 'pos_payments'), ('ix_pos_discounts_item_id', 'pos_discounts'),
        ('ix_pos_discounts_sale_id', 'pos_discounts'),
        ('ix_pos_sale_item_modifiers_item_id', 'pos_sale_item_modifiers'),
        ('ix_pos_sale_items_sale_id', 'pos_sale_items'), ('ix_pos_sales_opened_at', 'pos_sales'),
        ('ix_pos_sales_status', 'pos_sales'), ('ix_pos_sales_table_id', 'pos_sales'),
        ('ix_modifier_options_group_id', 'modifier_options'), ('ix_pos_tables_salon_id', 'pos_tables'),
    ]:
        op.drop_index(op.f(index), table_name=table)
    for table in ['pos_sale_events', 'pos_payments', 'pos_discounts', 'pos_sale_item_modifiers', 'pos_sale_items',
                  'pos_sales', 'discount_templates', 'payment_methods', 'product_modifier_groups',
                  'modifier_options', 'modifier_groups', 'pos_tables', 'salons']:
        op.drop_table(table)
