"""Add absence_requests table

Revision ID: add_absence_requests
Revises: merge_heads_feb27
Create Date: 2026-02-28 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_absence_requests'
down_revision = 'merge_heads_feb27'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('absence_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('employee_id', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('justification', sa.Text(), nullable=False),
    sa.Column('attachment_path', sa.Text(), nullable=True),
    sa.Column('attachment_filename', sa.String(length=255), nullable=True),
    sa.Column('attachment_mimetype', sa.String(length=100), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('reviewed_by_id', sa.Integer(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True),
    sa.Column('review_notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_absence_employee_dates', 'absence_requests', ['employee_id', 'start_date', 'end_date'], unique=False)
    op.create_index('idx_absence_status', 'absence_requests', ['status'], unique=False)
    op.create_index(op.f('ix_absence_requests_employee_id'), 'absence_requests', ['employee_id'], unique=False)
    op.create_index(op.f('ix_absence_requests_end_date'), 'absence_requests', ['end_date'], unique=False)
    op.create_index(op.f('ix_absence_requests_start_date'), 'absence_requests', ['start_date'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_absence_requests_start_date'), table_name='absence_requests')
    op.drop_index(op.f('ix_absence_requests_end_date'), table_name='absence_requests')
    op.drop_index(op.f('ix_absence_requests_employee_id'), table_name='absence_requests')
    op.drop_index('idx_absence_status', table_name='absence_requests')
    op.drop_index('idx_absence_employee_dates', table_name='absence_requests')
    op.drop_table('absence_requests')
