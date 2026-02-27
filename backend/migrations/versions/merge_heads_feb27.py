"""merge multiple heads

Revision ID: merge_heads_feb27
Revises: 1688e0c40534, add_store_hours_vacations
Create Date: 2026-02-27 19:18:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_heads_feb27'
down_revision = ('1688e0c40534', 'add_store_hours_vacations')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
