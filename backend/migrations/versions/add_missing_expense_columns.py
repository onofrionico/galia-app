"""Add missing columns to expenses table

Revision ID: add_missing_expense_columns
Revises: add_external_id_to_sales
Create Date: 2026-02-17 10:17:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_missing_expense_columns'
down_revision = 'add_external_id_to_sales'

def upgrade():
    # Check and add columns that might be missing
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('expenses')]
    
    if 'external_id' not in existing_columns:
        op.add_column('expenses', sa.Column('external_id', sa.Integer(), nullable=True))
        op.create_index(op.f('ix_expenses_external_id'), 'expenses', ['external_id'], unique=True)
    
    if 'categoria' not in existing_columns:
        op.add_column('expenses', sa.Column('categoria', sa.String(length=100), nullable=True))
    
    if 'subcategoria' not in existing_columns:
        op.add_column('expenses', sa.Column('subcategoria', sa.String(length=100), nullable=True))
    
    if 'estado_pago' not in existing_columns:
        op.add_column('expenses', sa.Column('estado_pago', sa.String(length=50), nullable=True, server_default='Pendiente'))
    
    if 'de_caja' not in existing_columns:
        op.add_column('expenses', sa.Column('de_caja', sa.Boolean(), nullable=True, server_default='false'))
    
    if 'caja' not in existing_columns:
        op.add_column('expenses', sa.Column('caja', sa.String(length=100), nullable=True))
    
    if 'numero_fiscal' not in existing_columns:
        op.add_column('expenses', sa.Column('numero_fiscal', sa.String(length=100), nullable=True))
    
    if 'tipo_comprobante' not in existing_columns:
        op.add_column('expenses', sa.Column('tipo_comprobante', sa.String(length=100), nullable=True))
    
    if 'numero_comprobante' not in existing_columns:
        op.add_column('expenses', sa.Column('numero_comprobante', sa.String(length=100), nullable=True))
    
    if 'creado_por' not in existing_columns:
        op.add_column('expenses', sa.Column('creado_por', sa.String(length=100), nullable=True))
    
    if 'cancelado' not in existing_columns:
        op.add_column('expenses', sa.Column('cancelado', sa.Boolean(), nullable=True, server_default='false'))

def downgrade():
    op.drop_column('expenses', 'cancelado')
    op.drop_column('expenses', 'creado_por')
    op.drop_column('expenses', 'numero_comprobante')
    op.drop_column('expenses', 'tipo_comprobante')
    op.drop_column('expenses', 'numero_fiscal')
    op.drop_column('expenses', 'caja')
    op.drop_column('expenses', 'de_caja')
    op.drop_column('expenses', 'estado_pago')
    op.drop_column('expenses', 'subcategoria')
    op.drop_column('expenses', 'categoria')
    op.drop_index(op.f('ix_expenses_external_id'), table_name='expenses')
    op.drop_column('expenses', 'external_id')
