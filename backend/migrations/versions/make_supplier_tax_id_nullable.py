"""make supplier tax_id nullable

Revision ID: make_tax_id_nullable
Revises: 
Create Date: 2026-03-17 21:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'make_tax_id_nullable'
down_revision = None  # Update this with the actual previous revision ID
branch_labels = None
depends_on = None


def upgrade():
    # Make tax_id nullable
    op.alter_column('suppliers', 'tax_id',
                    existing_type=sa.String(length=50),
                    nullable=True)


def downgrade():
    # Revert tax_id to NOT NULL
    op.alter_column('suppliers', 'tax_id',
                    existing_type=sa.String(length=50),
                    nullable=False)
