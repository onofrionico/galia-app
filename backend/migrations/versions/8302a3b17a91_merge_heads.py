"""merge heads

Revision ID: 8302a3b17a91
Revises: 584882ac450a, 9fbcd56354fa, abc123def456
Create Date: 2026-05-27 17:52:21.586808

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8302a3b17a91'
down_revision = ('584882ac450a', '9fbcd56354fa', 'abc123def456')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
