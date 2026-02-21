"""merge expense branches

Revision ID: merge_expense_branches
Revises: add_remaining_expense_columns, add_reports_module
Create Date: 2026-02-21 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_expense_branches'
down_revision = ('add_remaining_expense_columns', 'add_reports_module')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
