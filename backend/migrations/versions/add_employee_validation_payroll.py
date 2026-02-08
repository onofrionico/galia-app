"""Add employee validation fields to payroll

Revision ID: add_employee_validation
Revises: 1706d660ff20
Create Date: 2026-02-08 12:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_employee_validation'
down_revision = '1706d660ff20'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns exist before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('payrolls')]
    
    if 'employee_validated_at' not in columns:
        op.add_column('payrolls', 
            sa.Column('employee_validated_at', sa.DateTime(), nullable=True)
        )
    
    if 'employee_validated_by' not in columns:
        op.add_column('payrolls',
            sa.Column('employee_validated_by', sa.Integer(), nullable=True)
        )
        
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_payrolls_employee_validated_by',
            'payrolls', 'users',
            ['employee_validated_by'], ['id']
        )


def downgrade():
    op.drop_constraint('fk_payrolls_employee_validated_by', 'payrolls', type_='foreignkey')
    op.drop_column('payrolls', 'employee_validated_by')
    op.drop_column('payrolls', 'employee_validated_at')
