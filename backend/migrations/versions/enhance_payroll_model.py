"""enhance payroll model

Revision ID: enhance_payroll_001
Revises: 
Create Date: 2024-02-08 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'enhance_payroll_001'
down_revision = 'b020c4aff4de'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('payrolls', sa.Column('scheduled_hours', sa.Numeric(10, 2), nullable=False, server_default='0'))
    op.add_column('payrolls', sa.Column('status', sa.String(20), nullable=False, server_default='draft'))
    op.add_column('payrolls', sa.Column('validated_at', sa.DateTime(), nullable=True))
    op.add_column('payrolls', sa.Column('validated_by', sa.Integer(), nullable=True))
    op.add_column('payrolls', sa.Column('pdf_generated', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('payrolls', sa.Column('pdf_path', sa.Text(), nullable=True))
    op.add_column('payrolls', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('payrolls', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    op.create_foreign_key('fk_payrolls_validated_by', 'payrolls', 'users', ['validated_by'], ['id'])
    op.create_index('idx_payroll_status', 'payrolls', ['status'])


def downgrade():
    op.drop_index('idx_payroll_status', 'payrolls')
    op.drop_constraint('fk_payrolls_validated_by', 'payrolls', type_='foreignkey')
    
    op.drop_column('payrolls', 'updated_at')
    op.drop_column('payrolls', 'notes')
    op.drop_column('payrolls', 'pdf_path')
    op.drop_column('payrolls', 'pdf_generated')
    op.drop_column('payrolls', 'validated_by')
    op.drop_column('payrolls', 'validated_at')
    op.drop_column('payrolls', 'status')
    op.drop_column('payrolls', 'scheduled_hours')
