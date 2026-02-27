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
    # Check if columns exist before adding them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('expense_categories')]
    
    # Add expense_type column if it doesn't exist
    if 'expense_type' not in columns:
        op.add_column('expense_categories', 
            sa.Column('expense_type', sa.String(20), nullable=False, server_default='indirecto')
        )
    
    # Add created_at column if it doesn't exist
    if 'created_at' not in columns:
        op.add_column('expense_categories',
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
        )


def downgrade():
    # Check if columns exist before dropping them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('expense_categories')]
    
    if 'created_at' in columns:
        op.drop_column('expense_categories', 'created_at')
    if 'expense_type' in columns:
        op.drop_column('expense_categories', 'expense_type')
