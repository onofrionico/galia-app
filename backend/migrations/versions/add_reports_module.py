"""Add reports module tables (report_goals, dashboard_snapshots) and update expense_categories

Revision ID: add_reports_module
Revises: 
Create Date: 2026-02-14
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_reports_module'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add expense_type column to expense_categories if it doesn't exist
    try:
        op.add_column('expense_categories', 
            sa.Column('expense_type', sa.String(20), nullable=True, server_default='indirecto')
        )
    except Exception:
        pass  # Column might already exist
    
    # Add created_at column to expense_categories if it doesn't exist
    try:
        op.add_column('expense_categories',
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
        )
    except Exception:
        pass
    
    # Create report_goals table
    op.create_table('report_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('goal_type', sa.String(30), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False, server_default='mensual'),
        sa.Column('target_value', sa.Numeric(15, 2), nullable=False),
        sa.Column('target_unit', sa.String(20), nullable=False, server_default='monto'),
        sa.Column('comparison_type', sa.String(20), nullable=False, server_default='mayor_o_igual'),
        sa.Column('valid_from', sa.Date(), nullable=False, server_default=sa.text('CURRENT_DATE')),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], )
    )
    
    # Create indexes for report_goals
    op.create_index('idx_report_goals_active', 'report_goals', ['is_active', 'goal_type'])
    op.create_index('idx_report_goals_period', 'report_goals', ['valid_from', 'valid_to'])
    
    # Create dashboard_snapshots table
    op.create_table('dashboard_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('snapshot_date', 'period_type', name='uq_snapshot_date_period')
    )
    
    # Create index for dashboard_snapshots
    op.create_index('idx_dashboard_snapshots_date', 'dashboard_snapshots', ['snapshot_date', 'period_type'])


def downgrade():
    # Drop dashboard_snapshots
    op.drop_index('idx_dashboard_snapshots_date', table_name='dashboard_snapshots')
    op.drop_table('dashboard_snapshots')
    
    # Drop report_goals
    op.drop_index('idx_report_goals_period', table_name='report_goals')
    op.drop_index('idx_report_goals_active', table_name='report_goals')
    op.drop_table('report_goals')
    
    # Remove columns from expense_categories
    try:
        op.drop_column('expense_categories', 'expense_type')
        op.drop_column('expense_categories', 'created_at')
    except Exception:
        pass
