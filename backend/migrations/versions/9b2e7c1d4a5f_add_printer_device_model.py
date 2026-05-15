"""Add PrinterDevice model

Revision ID: 9b2e7c1d4a5f
Revises: fdab760911a3
Create Date: 2026-05-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b2e7c1d4a5f'
down_revision = 'fdab760911a3'
branch_labels = None
depends_on = None


def upgrade():
    # Create printer_devices table
    op.create_table(
        'printer_devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('ip_address', sa.String(length=100), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='offline'),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )


def downgrade():
    op.drop_table('printer_devices')
