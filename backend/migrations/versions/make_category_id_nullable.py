"""make category_id nullable in expenses

Revision ID: make_category_id_nullable
Revises: a60edab1e6c3
Create Date: 2026-02-26 13:26:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'make_category_id_nullable'
down_revision = 'a60edab1e6c3'
branch_labels = None
depends_on = None


def upgrade():
    # Make category_id nullable to allow importing expenses without category assignment
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.alter_column('category_id',
                              existing_type=sa.Integer(),
                              nullable=True)


def downgrade():
    # Revert category_id to NOT NULL
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.alter_column('category_id',
                              existing_type=sa.Integer(),
                              nullable=False)
