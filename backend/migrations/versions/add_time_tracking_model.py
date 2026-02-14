"""Add time tracking model for employee check-in/check-out

Revision ID: add_time_tracking
Revises: add_employee_mgmt
Create Date: 2026-02-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_time_tracking'
down_revision = 'add_employee_mgmt'
branch_labels = None
depends_on = None


def upgrade():
    # Create time_tracking table
    op.create_table('time_tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('tracking_date', sa.Date(), nullable=False),
        sa.Column('check_in', sa.Time(), nullable=True),
        sa.Column('check_out', sa.Time(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id', 'tracking_date', name='uq_employee_tracking_date')
    )
    op.create_index('idx_time_tracking_employee_date', 'time_tracking', ['employee_id', 'tracking_date'])


def downgrade():
    op.drop_index('idx_time_tracking_employee_date', table_name='time_tracking')
    op.drop_table('time_tracking')
