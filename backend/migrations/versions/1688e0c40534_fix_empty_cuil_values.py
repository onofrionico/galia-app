"""fix empty cuil values

Revision ID: 1688e0c40534
Revises: fab7ffda9936
Create Date: 2026-02-26 15:58:46.185328

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1688e0c40534'
down_revision = 'fab7ffda9936'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE employees 
        SET cuil = NULL 
        WHERE cuil = ''
    """)


def downgrade():
    pass
