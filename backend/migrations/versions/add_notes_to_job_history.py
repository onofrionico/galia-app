"""Add notes and created_by_id to employee_job_history

Revision ID: add_notes_job_history
Revises: add_employee_mgmt
Create Date: 2026-02-08 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_notes_job_history'
down_revision = 'add_employee_mgmt'
branch_labels = None
depends_on = None


def upgrade():
    # Add notes column
    op.add_column('employee_job_history', 
        sa.Column('notes', sa.Text(), nullable=True)
    )
    
    # Add created_by_id column
    op.add_column('employee_job_history',
        sa.Column('created_by_id', sa.Integer(), nullable=True)
    )
    
    # Add foreign key constraint for created_by_id
    op.create_foreign_key(
        'fk_employee_job_history_created_by',
        'employee_job_history', 'users',
        ['created_by_id'], ['id']
    )


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint('fk_employee_job_history_created_by', 'employee_job_history', type_='foreignkey')
    
    # Drop columns
    op.drop_column('employee_job_history', 'created_by_id')
    op.drop_column('employee_job_history', 'notes')
