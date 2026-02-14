"""merge_sales_module

Revision ID: 5f4b7f1abd00
Revises: add_employee_validation, update_sales_model
Create Date: 2026-02-14 10:45:08.751509

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f4b7f1abd00'
down_revision = ('add_employee_validation', 'update_sales_model')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
