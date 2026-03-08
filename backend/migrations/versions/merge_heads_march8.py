"""merge multiple heads march 8

Revision ID: merge_heads_march8
Revises: merge_categories_payroll, add_employee_documents
Create Date: 2026-03-08 11:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_heads_march8'
down_revision = ('merge_categories_payroll', 'add_employee_documents')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
