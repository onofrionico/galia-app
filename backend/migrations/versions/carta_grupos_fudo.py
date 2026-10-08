"""Carta: categorías desde Fudo y grupos de presentación

Revision ID: carta_grupos_fudo
Revises: add_menu_tables
Create Date: 2026-10-08

"""
from alembic import op
import sqlalchemy as sa


revision = 'carta_grupos_fudo'
down_revision = 'add_menu_tables'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'menu_groups',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(120), nullable=False, unique=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    with op.batch_alter_table('menu_categories') as batch:
        batch.add_column(sa.Column('fudo_category_id', sa.String(20), nullable=True))
        batch.add_column(sa.Column('group_id', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('show_title', sa.Boolean(), nullable=False, server_default=sa.true()))
        batch.add_column(sa.Column('fudo_status', sa.String(20), nullable=True))
        batch.create_unique_constraint('uq_menu_categories_fudo_category_id', ['fudo_category_id'])
        batch.create_foreign_key('fk_menu_categories_group_id', 'menu_groups', ['group_id'], ['id'], ondelete='SET NULL')
        batch.create_index('ix_menu_categories_group_id', ['group_id'])
    with op.batch_alter_table('menu_items') as batch:
        batch.add_column(sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    with op.batch_alter_table('fudo_products') as batch:
        batch.add_column(sa.Column('fudo_category_id', sa.String(20), nullable=True))
    # Lo existente se considera revisado (lo creó una persona).
    op.execute('UPDATE menu_items SET reviewed_at = updated_at')


def downgrade():
    with op.batch_alter_table('fudo_products') as batch:
        batch.drop_column('fudo_category_id')
    with op.batch_alter_table('menu_items') as batch:
        batch.drop_column('reviewed_at')
    with op.batch_alter_table('menu_categories') as batch:
        batch.drop_index('ix_menu_categories_group_id')
        batch.drop_constraint('fk_menu_categories_group_id', type_='foreignkey')
        batch.drop_constraint('uq_menu_categories_fudo_category_id', type_='unique')
        batch.drop_column('fudo_status')
        batch.drop_column('show_title')
        batch.drop_column('group_id')
        batch.drop_column('fudo_category_id')
    op.drop_table('menu_groups')
