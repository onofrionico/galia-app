"""Add app_settings table

Revision ID: add_app_settings_table
Revises: add_employee_validation, add_reports_module
Create Date: 2026-02-15 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_app_settings_table'
down_revision = ('add_employee_validation', 'add_reports_module')
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('app_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('primary_color', sa.String(length=7), nullable=True),
    sa.Column('secondary_color', sa.String(length=7), nullable=True),
    sa.Column('accent_color', sa.String(length=7), nullable=True),
    sa.Column('logo_url', sa.String(length=500), nullable=True),
    sa.Column('cafeteria_name', sa.String(length=200), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('app_settings')
