"""Add digital menu (carta) tables

Revision ID: add_menu_tables
Revises: merge_heads_march8
Create Date: 2026-10-07

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_menu_tables'
down_revision = 'merge_heads_march8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'menu_categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(120), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        'menu_tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('slug', sa.String(60), nullable=False, unique=True),
        sa.Column('color', sa.String(7), nullable=False, server_default='#5C2E46'),
    )
    op.create_table(
        'fudo_products',
        sa.Column('fudo_id', sa.String(20), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('category_name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('ignored', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('synced_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        'menu_settings',
        sa.Column('key', sa.String(50), primary_key=True),
        sa.Column('value', sa.Text(), nullable=True),
    )
    op.create_table(
        'menu_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('menu_categories.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_key', sa.String(300), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_menu_items_category_id', 'menu_items', ['category_id'])
    op.create_table(
        'menu_item_variants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('menu_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('label', sa.String(100), nullable=True),
        sa.Column('fudo_product_id', sa.String(20), nullable=True, unique=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('fudo_status', sa.String(20), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_menu_item_variants_item_id', 'menu_item_variants', ['item_id'])
    op.create_table(
        'menu_item_tags',
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('menu_items.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('menu_tags.id', ondelete='CASCADE'), primary_key=True),
    )


def downgrade():
    op.drop_table('menu_item_tags')
    op.drop_index('ix_menu_item_variants_item_id', table_name='menu_item_variants')
    op.drop_table('menu_item_variants')
    op.drop_index('ix_menu_items_category_id', table_name='menu_items')
    op.drop_table('menu_items')
    op.drop_table('menu_settings')
    op.drop_table('fudo_products')
    op.drop_table('menu_tags')
    op.drop_table('menu_categories')
