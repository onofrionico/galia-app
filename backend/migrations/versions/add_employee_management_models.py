"""Add employee management models with job positions and history

Revision ID: add_employee_mgmt
Revises: b020c4aff4de
Create Date: 2026-02-05 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_employee_mgmt'
down_revision = 'b020c4aff4de'
branch_labels = None
depends_on = None


def upgrade():
    # Create job_positions table
    op.create_table('job_positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contract_type', sa.String(20), nullable=False),
        sa.Column('base_salary', sa.Numeric(10, 2), nullable=True),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('standard_hours_per_week', sa.Integer(), nullable=True),
        sa.Column('standard_hours_per_month', sa.Integer(), nullable=True),
        sa.Column('overtime_rate_multiplier', sa.Numeric(3, 2), nullable=True),
        sa.Column('weekend_rate_multiplier', sa.Numeric(3, 2), nullable=True),
        sa.Column('holiday_rate_multiplier', sa.Numeric(3, 2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_job_positions_is_active', 'job_positions', ['is_active'])

    # Create employee_job_history table
    op.create_table('employee_job_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('job_position_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_position_id'], ['job_positions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_employee_job_history_employee_id', 'employee_job_history', ['employee_id'])
    op.create_index('ix_employee_job_history_job_position_id', 'employee_job_history', ['job_position_id'])


def downgrade():
    op.drop_index('ix_employee_job_history_job_position_id', table_name='employee_job_history')
    op.drop_index('ix_employee_job_history_employee_id', table_name='employee_job_history')
    op.drop_table('employee_job_history')
    op.drop_index('ix_job_positions_is_active', table_name='job_positions')
    op.drop_table('job_positions')
