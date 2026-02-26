"""add_expense_type_to_categories

Revision ID: fab7ffda9936
Revises: make_category_id_nullable
Create Date: 2026-02-26 13:49:37.493510

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fab7ffda9936'
down_revision = 'make_category_id_nullable'
branch_labels = None
depends_on = None


def upgrade():
    # Add expense_type column
    op.add_column('expense_categories', 
        sa.Column('expense_type', sa.String(20), nullable=False, server_default='indirecto')
    )
    
    # Add created_at column
    op.add_column('expense_categories',
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )


def downgrade():
    op.drop_column('expense_categories', 'created_at')
    op.drop_column('expense_categories', 'expense_type')
