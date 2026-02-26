"""merge expense migrations

Revision ID: a60edab1e6c3
Revises: e3b2bf1b3d92, remove_old_expense_columns
Create Date: 2026-02-26 13:24:56.467552

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a60edab1e6c3'
down_revision = ('e3b2bf1b3d92', 'remove_old_expense_columns')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
