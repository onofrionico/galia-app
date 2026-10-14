"""add print stations, printers, print jobs, points and QZ keys; station on product categories

Revision ID: b3a0_add_print_stations
Revises: b2b0_products_fudo_link
Create Date: 2026-10-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b3a0_add_print_stations'
down_revision = 'b2b0_products_fudo_link'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'print_stations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=60), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'printers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=60), nullable=False),
        sa.Column('connection', sa.String(length=10), nullable=False),
        sa.Column('host', sa.String(length=100), nullable=True),
        sa.Column('port', sa.Integer(), nullable=False, server_default='9100'),
        sa.Column('os_name', sa.String(length=120), nullable=True),
        sa.Column('paper_width', sa.Integer(), nullable=False, server_default='80'),
        sa.Column('print_point', sa.String(length=60), nullable=False),
        sa.Column('station_id', sa.Integer(), sa.ForeignKey('print_stations.id'), nullable=True),
        sa.Column('is_cashier', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'print_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('printer_id', sa.Integer(), sa.ForeignKey('printers.id'), nullable=False),
        sa.Column('sale_id', sa.Integer(), sa.ForeignKey('pos_sales.id'), nullable=True),
        sa.Column('station_id', sa.Integer(), sa.ForeignKey('print_stations.id'), nullable=True),
        sa.Column('batch', sa.Integer(), nullable=True),
        sa.Column('document', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error', sa.String(length=255), nullable=True),
        sa.Column('claimed_by', sa.String(length=60), nullable=True),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.Column('printed_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('reprint_of', sa.Integer(), sa.ForeignKey('print_jobs.id'), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_print_jobs_printer_id', 'print_jobs', ['printer_id'])
    op.create_index('ix_print_jobs_sale_id', 'print_jobs', ['sale_id'])
    op.create_index('ix_print_jobs_printer_status', 'print_jobs', ['printer_id', 'status', 'id'])
    op.create_table(
        'print_points',
        sa.Column('name', sa.String(length=60), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('name'),
    )
    op.create_table(
        'qz_signing_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('certificate', sa.Text(), nullable=False),
        sa.Column('private_key', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('product_categories') as batch:
        batch.add_column(sa.Column('station_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_product_categories_station_id', 'print_stations', ['station_id'], ['id'])


def downgrade():
    with op.batch_alter_table('product_categories') as batch:
        batch.drop_constraint('fk_product_categories_station_id', type_='foreignkey')
        batch.drop_column('station_id')
    op.drop_table('qz_signing_keys')
    op.drop_table('print_points')
    op.drop_index('ix_print_jobs_printer_status', table_name='print_jobs')
    op.drop_index('ix_print_jobs_sale_id', table_name='print_jobs')
    op.drop_index('ix_print_jobs_printer_id', table_name='print_jobs')
    op.drop_table('print_jobs')
    op.drop_table('printers')
    op.drop_table('print_stations')
