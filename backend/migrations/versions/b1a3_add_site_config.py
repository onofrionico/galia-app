"""add site_config table for branding

Revision ID: b1a3_add_site_config
Revises: b1a2_add_products_and_supplies
Create Date: 2026-10-08 00:00:03.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b1a3_add_site_config'
down_revision = 'b1a2_add_products_and_supplies'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'site_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('logo_path', sa.String(length=255), nullable=True),
        sa.Column('banner_background_path', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('site_config')
