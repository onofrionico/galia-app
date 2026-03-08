"""Merge categories migration with payroll claims branch

Revision ID: merge_categories_payroll
Revises: migrate_to_normalized_categories, add_payroll_claims
Create Date: 2026-03-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_categories_payroll'
down_revision = ('migrate_to_normalized_categories', 'add_payroll_claims')
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration, no changes needed
    pass


def downgrade():
    # This is a merge migration, no changes needed
    pass
