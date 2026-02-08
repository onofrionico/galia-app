"""merge_migrations

Revision ID: 1706d660ff20
Revises: add_notes_job_history, enhance_payroll_001
Create Date: 2026-02-08 12:22:12.092389

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1706d660ff20'
down_revision = ('add_notes_job_history', 'enhance_payroll_001')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
