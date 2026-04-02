"""merge_migration_heads

Revision ID: fa83c4360922
Revises: e8cb547a5380, make_tax_id_nullable, merge_heads_march8
Create Date: 2026-03-26 17:11:08.142428

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa83c4360922'
down_revision = ('e8cb547a5380', 'make_tax_id_nullable', 'merge_heads_march8')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
