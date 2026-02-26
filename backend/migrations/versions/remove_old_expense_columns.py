"""remove old expense columns

Revision ID: remove_old_expense_columns
Revises: add_remaining_expense_columns
Create Date: 2026-02-26 12:14:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_old_expense_columns'
down_revision = 'add_remaining_expense_columns'
branch_labels = None
depends_on = None


def upgrade():
    # Remove old columns that conflict with the new structure
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        # Drop old columns from initial migration
        batch_op.drop_column('amount')
        batch_op.drop_column('expense_date')
        batch_op.drop_column('description')
        batch_op.drop_column('supplier')
        batch_op.drop_column('created_by')


def downgrade():
    # Add back old columns if needed
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_by', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('supplier', sa.String(200), nullable=True))
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('expense_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('amount', sa.Numeric(10, 2), nullable=True))
