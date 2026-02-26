"""Add sunday_rate_multiplier to job_positions

Revision ID: e3b2bf1b3d92
Revises: make_employee_fields_optional
Create Date: 2026-02-25 23:54:34.259333

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3b2bf1b3d92'
down_revision = 'make_employee_fields_optional'
branch_labels = None
depends_on = None


def upgrade():
    # Add sunday_rate_multiplier column to job_positions table
    op.add_column('job_positions', sa.Column('sunday_rate_multiplier', sa.Numeric(precision=3, scale=2), nullable=True))
    
    # Set default value of 1.0 for existing records
    op.execute("UPDATE job_positions SET sunday_rate_multiplier = 1.0 WHERE sunday_rate_multiplier IS NULL")


def downgrade():
    # Remove sunday_rate_multiplier column from job_positions table
    op.drop_column('job_positions', 'sunday_rate_multiplier')
