"""merge suppliers and march8 heads

Revision ID: e8cb547a5380
Revises: create_suppliers_module, add_payroll_claims
Create Date: 2026-03-17 21:34:48.823622

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8cb547a5380'
down_revision = ('create_suppliers_module', 'add_payroll_claims')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
