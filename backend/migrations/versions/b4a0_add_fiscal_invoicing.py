"""add fiscal settings, ARCA tokens, fiscal customers, invoices; payment_methods.invoiced_externally

Revision ID: b4a0_add_fiscal_invoicing
Revises: b3a0_add_print_stations
Create Date: 2026-10-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b4a0_add_fiscal_invoicing'
down_revision = 'b3a0_add_print_stations'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'fiscal_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cuit', sa.String(length=11), nullable=True),
        sa.Column('business_name', sa.String(length=120), nullable=True),
        sa.Column('address', sa.String(length=200), nullable=True),
        sa.Column('gross_income', sa.String(length=40), nullable=True),
        sa.Column('activity_start', sa.Date(), nullable=True),
        sa.Column('iva_condition', sa.String(length=30), nullable=False, server_default='monotributo'),
        sa.Column('point_of_sale', sa.Integer(), nullable=True),
        sa.Column('environment', sa.String(length=15), nullable=False, server_default='homologacion'),
        sa.Column('cf_id_threshold', sa.Numeric(14, 2), nullable=True),
        sa.Column('default_iva_rate', sa.Numeric(5, 2), nullable=False, server_default='21'),
        sa.Column('homo_private_key', sa.Text(), nullable=True),
        sa.Column('homo_csr', sa.Text(), nullable=True),
        sa.Column('homo_certificate', sa.Text(), nullable=True),
        sa.Column('homo_cert_expires_at', sa.DateTime(), nullable=True),
        sa.Column('prod_private_key', sa.Text(), nullable=True),
        sa.Column('prod_csr', sa.Text(), nullable=True),
        sa.Column('prod_certificate', sa.Text(), nullable=True),
        sa.Column('prod_cert_expires_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'arca_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service', sa.String(length=20), nullable=False),
        sa.Column('environment', sa.String(length=15), nullable=False),
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('sign', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('service', 'environment', name='uq_arca_tokens_service_env'),
    )
    op.create_table(
        'fiscal_customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doc_type', sa.String(length=5), nullable=False),
        sa.Column('doc_number', sa.String(length=11), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('iva_condition', sa.String(length=30), nullable=False),
        sa.Column('address', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('doc_type', 'doc_number', name='uq_fiscal_customers_doc'),
    )
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=15), nullable=False),
        sa.Column('voucher_type', sa.Integer(), nullable=False),
        sa.Column('environment', sa.String(length=15), nullable=False),
        sa.Column('point_of_sale', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), sa.ForeignKey('pos_sales.id'), nullable=True),
        sa.Column('related_invoice_id', sa.Integer(), sa.ForeignKey('invoices.id'), nullable=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('fiscal_customers.id'), nullable=True),
        sa.Column('receiver_doc_type', sa.Integer(), nullable=False),
        sa.Column('receiver_doc_number', sa.String(length=11), nullable=False),
        sa.Column('receiver_name', sa.String(length=120), nullable=False),
        sa.Column('receiver_iva_condition', sa.String(length=30), nullable=False),
        sa.Column('receiver_address', sa.String(length=200), nullable=True),
        sa.Column('detail_mode', sa.String(length=10), nullable=False),
        sa.Column('lines', sa.JSON(), nullable=False),
        sa.Column('total', sa.Numeric(14, 2), nullable=False),
        sa.Column('net', sa.Numeric(14, 2), nullable=False),
        sa.Column('iva', sa.Numeric(14, 2), nullable=False),
        sa.Column('iva_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('voucher_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('cae', sa.String(length=20), nullable=True),
        sa.Column('cae_due', sa.Date(), nullable=True),
        sa.Column('arca_result', sa.JSON(), nullable=True),
        sa.Column('request', sa.JSON(), nullable=False),
        sa.Column('error', sa.String(length=500), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('authorized_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_invoices_sale_id', 'invoices', ['sale_id'])
    op.create_index('ix_invoices_related_invoice_id', 'invoices', ['related_invoice_id'])
    op.create_index('uq_invoices_authorized_number', 'invoices',
                    ['environment', 'point_of_sale', 'voucher_type', 'number'], unique=True,
                    postgresql_where=sa.text("status = 'authorized'"),
                    sqlite_where=sa.text("status = 'authorized'"))
    op.create_table(
        'invoice_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('invoices.id'), nullable=False),
        sa.Column('payment_id', sa.Integer(), sa.ForeignKey('pos_payments.id'), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_invoice_payments_invoice_id', 'invoice_payments', ['invoice_id'])
    op.create_index('ix_invoice_payments_payment_id', 'invoice_payments', ['payment_id'])
    with op.batch_alter_table('payment_methods') as batch:
        batch.add_column(sa.Column('invoiced_externally', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.execute("UPDATE payment_methods SET invoiced_externally = false WHERE kind = 'cash'")


def downgrade():
    with op.batch_alter_table('payment_methods') as batch:
        batch.drop_column('invoiced_externally')
    op.drop_index('ix_invoice_payments_payment_id', table_name='invoice_payments')
    op.drop_index('ix_invoice_payments_invoice_id', table_name='invoice_payments')
    op.drop_table('invoice_payments')
    op.drop_index('uq_invoices_authorized_number', table_name='invoices')
    op.drop_index('ix_invoices_related_invoice_id', table_name='invoices')
    op.drop_index('ix_invoices_sale_id', table_name='invoices')
    op.drop_table('invoices')
    op.drop_table('fiscal_customers')
    op.drop_table('arca_tokens')
    op.drop_table('fiscal_settings')
