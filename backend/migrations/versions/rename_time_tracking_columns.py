"""Rename time_tracking columns from check_in/check_out to actual_check_in/actual_check_out

Revision ID: rename_time_tracking_columns
Revises: add_time_tracking
Create Date: 2026-02-06 11:11:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rename_time_tracking_columns'
down_revision = 'add_time_tracking'
branch_labels = None
depends_on = None


def upgrade():
    # Rename check_in to actual_check_in
    op.alter_column('time_tracking', 'check_in',
               new_column_name='actual_check_in',
               existing_type=sa.Time(),
               existing_nullable=True)
    
    # Rename check_out to actual_check_out
    op.alter_column('time_tracking', 'check_out',
               new_column_name='actual_check_out',
               existing_type=sa.Time(),
               existing_nullable=True)


def downgrade():
    # Rename actual_check_in back to check_in
    op.alter_column('time_tracking', 'actual_check_in',
               new_column_name='check_in',
               existing_type=sa.Time(),
               existing_nullable=True)
    
    # Rename actual_check_out back to check_out
    op.alter_column('time_tracking', 'actual_check_out',
               new_column_name='check_out',
               existing_type=sa.Time(),
               existing_nullable=True)
