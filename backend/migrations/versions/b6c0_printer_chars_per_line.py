"""printers.chars_per_line (caracteres por renglón; nulo = según el papel)

Revision ID: b6c0_printer_chars_per_line
Revises: b6b0_printer_is_kitchen
Create Date: 2026-10-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b6c0_printer_chars_per_line'
down_revision = 'b6b0_printer_is_kitchen'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('printers', sa.Column('chars_per_line', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('printers', 'chars_per_line')
