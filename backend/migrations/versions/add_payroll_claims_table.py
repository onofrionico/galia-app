"""Add payroll_claims table for dispute management

Revision ID: add_payroll_claims
Revises: add_absence_requests
Create Date: 2026-03-04 01:12:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_payroll_claims'
down_revision = 'add_absence_requests'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('payroll_claims',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payroll_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('claim_reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('admin_response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['payroll_id'], ['payrolls.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_claim_status', 'payroll_claims', ['status'], unique=False)
    op.create_index('idx_claim_payroll', 'payroll_claims', ['payroll_id'], unique=False)


def downgrade():
    op.drop_index('idx_claim_payroll', table_name='payroll_claims')
    op.drop_index('idx_claim_status', table_name='payroll_claims')
    op.drop_table('payroll_claims')
