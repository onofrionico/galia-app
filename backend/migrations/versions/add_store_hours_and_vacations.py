"""add store hours and vacation periods

Revision ID: add_store_hours_vacations
Revises: add_reports_module
Create Date: 2026-02-27 13:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_store_hours_vacations'
down_revision = 'add_reports_module'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla store_hours
    op.create_table('store_hours',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_name', sa.String(length=100), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('opening_time', sa.Time(), nullable=False),
        sa.Column('closing_time', sa.Time(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Crear tabla vacation_periods
    op.create_table('vacation_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='aprobado'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Crear índices
    op.create_index('idx_store_hours_location', 'store_hours', ['location_name', 'is_active'])
    op.create_index('idx_vacation_periods_employee', 'vacation_periods', ['employee_id', 'status'])
    op.create_index('idx_vacation_periods_dates', 'vacation_periods', ['start_date', 'end_date'])


def downgrade():
    op.drop_index('idx_vacation_periods_dates', table_name='vacation_periods')
    op.drop_index('idx_vacation_periods_employee', table_name='vacation_periods')
    op.drop_index('idx_store_hours_location', table_name='store_hours')
    op.drop_table('vacation_periods')
    op.drop_table('store_hours')
