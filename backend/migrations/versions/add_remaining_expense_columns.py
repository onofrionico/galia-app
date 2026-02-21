"""Add remaining expense columns matching the model

Revision ID: add_remaining_expense_columns
Revises: add_missing_expense_columns
Create Date: 2026-02-17 10:51:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_remaining_expense_columns'
down_revision = 'add_missing_expense_columns'

def upgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('expenses')]
    
    # Add columns that match the Expense model
    if 'fecha' not in existing_columns:
        op.add_column('expenses', sa.Column('fecha', sa.Date(), nullable=True))
        op.create_index(op.f('ix_expenses_fecha'), 'expenses', ['fecha'], unique=False)
    
    if 'fecha_vencimiento' not in existing_columns:
        op.add_column('expenses', sa.Column('fecha_vencimiento', sa.Date(), nullable=True))
    
    if 'proveedor' not in existing_columns:
        op.add_column('expenses', sa.Column('proveedor', sa.String(length=200), nullable=True))
    
    if 'comentario' not in existing_columns:
        op.add_column('expenses', sa.Column('comentario', sa.Text(), nullable=True))
    
    if 'importe' not in existing_columns:
        op.add_column('expenses', sa.Column('importe', sa.Numeric(12, 2), nullable=True))
    
    if 'medio_pago' not in existing_columns:
        op.add_column('expenses', sa.Column('medio_pago', sa.String(length=100), nullable=True))
    
    # Copy data from old columns to new columns if they exist
    if 'expense_date' in existing_columns and 'fecha' in [col['name'] for col in inspector.get_columns('expenses')]:
        op.execute('UPDATE expenses SET fecha = expense_date WHERE fecha IS NULL')
    
    if 'amount' in existing_columns and 'importe' in [col['name'] for col in inspector.get_columns('expenses')]:
        op.execute('UPDATE expenses SET importe = amount WHERE importe IS NULL')
    
    if 'supplier' in existing_columns and 'proveedor' in [col['name'] for col in inspector.get_columns('expenses')]:
        op.execute('UPDATE expenses SET proveedor = supplier WHERE proveedor IS NULL')
    
    if 'description' in existing_columns and 'comentario' in [col['name'] for col in inspector.get_columns('expenses')]:
        op.execute('UPDATE expenses SET comentario = description WHERE comentario IS NULL')

def downgrade():
    op.drop_index(op.f('ix_expenses_fecha'), table_name='expenses')
    op.drop_column('expenses', 'medio_pago')
    op.drop_column('expenses', 'importe')
    op.drop_column('expenses', 'comentario')
    op.drop_column('expenses', 'proveedor')
    op.drop_column('expenses', 'fecha_vencimiento')
    op.drop_column('expenses', 'fecha')
