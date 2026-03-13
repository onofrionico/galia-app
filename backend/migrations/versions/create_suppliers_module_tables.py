"""create suppliers module tables

Revision ID: create_suppliers_module
Revises: merge_heads_march8
Create Date: 2026-03-13 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_suppliers_module'
down_revision = 'merge_heads_march8'
branch_labels = None
depends_on = None


def upgrade():
    # Create suppliers table
    op.create_table('suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('tax_id', sa.String(length=50), nullable=False),
        sa.Column('contact_person', sa.String(length=200), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('payment_terms', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('modified_by_user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tax_id'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['modified_by_user_id'], ['users.id'], )
    )
    op.create_index('idx_suppliers_name', 'suppliers', ['name'])
    op.create_index('idx_suppliers_status', 'suppliers', ['status'])
    op.create_index('idx_suppliers_is_deleted', 'suppliers', ['is_deleted'])

    # Create product_masters table
    op.create_table('product_masters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('unit_of_measure', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], )
    )
    op.create_index('idx_product_masters_name', 'product_masters', ['name'])
    op.create_index('idx_product_masters_category', 'product_masters', ['category'])

    # Create products table
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('product_master_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('sku', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('unit_of_measure', sa.String(length=50), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('modified_by_user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ),
        sa.ForeignKeyConstraint(['product_master_id'], ['product_masters.id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['modified_by_user_id'], ['users.id'], ),
        sa.UniqueConstraint('supplier_id', 'sku', name='uq_supplier_sku')
    )
    op.create_index('idx_products_supplier_id', 'products', ['supplier_id'])
    op.create_index('idx_products_product_master_id', 'products', ['product_master_id'])
    op.create_index('idx_products_name', 'products', ['name'])
    op.create_index('idx_products_sku', 'products', ['sku'])
    op.create_index('idx_products_status', 'products', ['status'])
    op.create_index('idx_products_is_deleted', 'products', ['is_deleted'])

    # Create purchases table
    op.create_table('purchases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('related_expense_id', sa.Integer(), nullable=True),
        sa.Column('purchase_date', sa.Date(), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='ARS'),
        sa.Column('exchange_rate', sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column('invoice_number', sa.String(length=100), nullable=True),
        sa.Column('cae_number', sa.String(length=100), nullable=True),
        sa.Column('payment_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('modified_by_user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ),
        sa.ForeignKeyConstraint(['related_expense_id'], ['expenses.id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['modified_by_user_id'], ['users.id'], )
    )
    op.create_index('idx_purchases_supplier_id', 'purchases', ['supplier_id'])
    op.create_index('idx_purchases_purchase_date', 'purchases', ['purchase_date'])
    op.create_index('idx_purchases_payment_status', 'purchases', ['payment_status'])
    op.create_index('idx_purchases_is_deleted', 'purchases', ['is_deleted'])
    op.create_index('idx_purchases_related_expense_id', 'purchases', ['related_expense_id'])

    # Create purchase_items table
    op.create_table('purchase_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('purchase_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('product_name_snapshot', sa.String(length=200), nullable=False),
        sa.Column('sku_snapshot', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('catalog_price_at_time', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['purchase_id'], ['purchases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], )
    )
    op.create_index('idx_purchase_items_purchase_id', 'purchase_items', ['purchase_id'])
    op.create_index('idx_purchase_items_product_id', 'purchase_items', ['product_id'])

    # Create price_history table
    op.create_table('price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('change_percentage', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('related_purchase_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['related_purchase_id'], ['purchases.id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], )
    )
    op.create_index('idx_price_history_product_id', 'price_history', ['product_id'])
    op.create_index('idx_price_history_effective_date', 'price_history', ['effective_date'])
    op.create_index('idx_price_history_source', 'price_history', ['source'])

    # Create exchange_rates table
    op.create_table('exchange_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_currency', sa.String(length=10), nullable=False),
        sa.Column('to_currency', sa.String(length=10), nullable=False),
        sa.Column('rate', sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False, server_default='manual'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.UniqueConstraint('from_currency', 'to_currency', 'effective_date', name='uq_exchange_rate_date')
    )
    op.create_index('idx_exchange_rates_currencies', 'exchange_rates', ['from_currency', 'to_currency'])
    op.create_index('idx_exchange_rates_effective_date', 'exchange_rates', ['effective_date'])

    # Create configurable_lists table
    op.create_table('configurable_lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('list_type', sa.String(length=50), nullable=False),
        sa.Column('value', sa.String(length=200), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.UniqueConstraint('list_type', 'value', name='uq_list_type_value')
    )
    op.create_index('idx_configurable_lists_type', 'configurable_lists', ['list_type'])
    op.create_index('idx_configurable_lists_is_active', 'configurable_lists', ['is_active'])

    # Create audit_log table (optional but recommended)
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    op.create_index('idx_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('configurable_lists')
    op.drop_table('exchange_rates')
    op.drop_table('price_history')
    op.drop_table('purchase_items')
    op.drop_table('purchases')
    op.drop_table('products')
    op.drop_table('product_masters')
    op.drop_table('suppliers')
