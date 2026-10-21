"""Fudo cutover: operation settings, import months, practice flags, menu links to the Galia catalog

Revision ID: b6a0_fudo_cutover
Revises: b5d0_add_sale_items
Create Date: 2026-10-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b6a0_fudo_cutover'
down_revision = 'b5d0_add_sale_items'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'operation_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('catalog_in_galia', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('fudo_off', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('practice_mode', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'fudo_import_months',
        sa.Column('month', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False, server_default='pending'),
        sa.Column('fudo_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('fudo_total', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('galia_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('galia_total', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('changed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('imported_at', sa.DateTime(), nullable=True),
        sa.Column('run_id', sa.Integer(), sa.ForeignKey('fudo_sync_runs.id'), nullable=True),
        sa.PrimaryKeyConstraint('month'),
    )
    with op.batch_alter_table('pos_sales') as batch:
        batch.add_column(sa.Column('is_practice', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.create_index('ix_pos_sales_is_practice', ['is_practice'])
    with op.batch_alter_table('cash_sessions') as batch:
        batch.add_column(sa.Column('is_practice', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.create_index('ix_cash_sessions_is_practice', ['is_practice'])
    with op.batch_alter_table('product_variants') as batch:
        batch.add_column(sa.Column('menu_ignored', sa.Boolean(), nullable=False, server_default=sa.false()))
    with op.batch_alter_table('menu_item_variants') as batch:
        batch.add_column(sa.Column('product_variant_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_menu_item_variants_product_variant', 'product_variants',
                                 ['product_variant_id'], ['id'], ondelete='SET NULL')
        batch.create_unique_constraint('uq_menu_item_variants_product_variant', ['product_variant_id'])
    with op.batch_alter_table('menu_categories') as batch:
        batch.add_column(sa.Column('product_category_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_menu_categories_product_category', 'product_categories',
                                 ['product_category_id'], ['id'], ondelete='SET NULL')
        batch.create_unique_constraint('uq_menu_categories_product_category', ['product_category_id'])


def downgrade():
    with op.batch_alter_table('menu_categories') as batch:
        batch.drop_constraint('uq_menu_categories_product_category', type_='unique')
        batch.drop_constraint('fk_menu_categories_product_category', type_='foreignkey')
        batch.drop_column('product_category_id')
    with op.batch_alter_table('menu_item_variants') as batch:
        batch.drop_constraint('uq_menu_item_variants_product_variant', type_='unique')
        batch.drop_constraint('fk_menu_item_variants_product_variant', type_='foreignkey')
        batch.drop_column('product_variant_id')
    with op.batch_alter_table('product_variants') as batch:
        batch.drop_column('menu_ignored')
    with op.batch_alter_table('cash_sessions') as batch:
        batch.drop_index('ix_cash_sessions_is_practice')
        batch.drop_column('is_practice')
    with op.batch_alter_table('pos_sales') as batch:
        batch.drop_index('ix_pos_sales_is_practice')
        batch.drop_column('is_practice')
    op.drop_table('fudo_import_months')
    op.drop_table('operation_settings')
