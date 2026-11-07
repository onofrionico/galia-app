"""schedules.is_public (grilla visible para todos los empleados)

Revision ID: b6e0_schedule_is_public
Revises: b6c0_printer_chars_per_line
Create Date: 2026-11-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b6e0_schedule_is_public'
down_revision = 'b6c0_printer_chars_per_line'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'schedules',
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column('schedules', 'is_public')
