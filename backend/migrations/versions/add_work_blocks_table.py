"""Add work_blocks table for multiple work hours per day

Revision ID: add_work_blocks
Revises: rename_time_tracking_columns
Create Date: 2026-02-06 11:37:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_work_blocks'
down_revision = 'rename_time_tracking_columns'
branch_labels = None
depends_on = None


def upgrade():
    # Create work_blocks table
    op.create_table('work_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('time_tracking_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['time_tracking_id'], ['time_tracking.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_work_blocks_time_tracking', 'work_blocks', ['time_tracking_id'])


def downgrade():
    op.drop_index('idx_work_blocks_time_tracking', table_name='work_blocks')
    op.drop_table('work_blocks')
