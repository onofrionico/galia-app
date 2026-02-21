"""Add fecha column to sales table

Revision ID: add_fecha_to_sales
Revises: add_remaining_expense_columns
Create Date: 2026-02-17 12:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_fecha_to_sales'
down_revision = 'add_remaining_expense_columns'

def upgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('sales')]
    
    # Add fecha column if it doesn't exist
    if 'fecha' not in existing_columns:
        op.add_column('sales', sa.Column('fecha', sa.Date(), nullable=True))
        op.create_index(op.f('ix_sales_fecha'), 'sales', ['fecha'], unique=False)
        
        # Copy data from sale_date if it exists
        if 'sale_date' in existing_columns:
            op.execute('UPDATE sales SET fecha = sale_date WHERE fecha IS NULL')
    
    # Add other missing columns that match the Sale model
    if 'creacion' not in existing_columns:
        op.add_column('sales', sa.Column('creacion', sa.DateTime(), nullable=True))
        if 'created_at' in existing_columns:
            op.execute('UPDATE sales SET creacion = created_at WHERE creacion IS NULL')
    
    if 'cerrada' not in existing_columns:
        op.add_column('sales', sa.Column('cerrada', sa.DateTime(), nullable=True))
    
    if 'caja' not in existing_columns:
        op.add_column('sales', sa.Column('caja', sa.String(length=100), nullable=True))
    
    if 'estado' not in existing_columns:
        op.add_column('sales', sa.Column('estado', sa.String(length=50), nullable=True, server_default='En curso'))
    
    if 'cliente' not in existing_columns:
        op.add_column('sales', sa.Column('cliente', sa.String(length=200), nullable=True))
    
    if 'mesa' not in existing_columns:
        op.add_column('sales', sa.Column('mesa', sa.String(length=20), nullable=True))
    
    if 'sala' not in existing_columns:
        op.add_column('sales', sa.Column('sala', sa.String(length=100), nullable=True))
    
    if 'personas' not in existing_columns:
        op.add_column('sales', sa.Column('personas', sa.Integer(), nullable=True))
    
    if 'camarero' not in existing_columns:
        op.add_column('sales', sa.Column('camarero', sa.String(length=200), nullable=True))
    
    if 'medio_pago' not in existing_columns:
        op.add_column('sales', sa.Column('medio_pago', sa.String(length=100), nullable=True))
    
    if 'total' not in existing_columns:
        op.add_column('sales', sa.Column('total', sa.Numeric(12, 2), nullable=True, server_default='0'))
    
    if 'fiscal' not in existing_columns:
        op.add_column('sales', sa.Column('fiscal', sa.Boolean(), nullable=True, server_default='false'))
    
    if 'tipo_venta' not in existing_columns:
        op.add_column('sales', sa.Column('tipo_venta', sa.String(length=50), nullable=True, server_default='Local'))
    
    if 'comentario' not in existing_columns:
        op.add_column('sales', sa.Column('comentario', sa.Text(), nullable=True))
    
    if 'origen' not in existing_columns:
        op.add_column('sales', sa.Column('origen', sa.String(length=100), nullable=True))
    
    if 'id_origen' not in existing_columns:
        op.add_column('sales', sa.Column('id_origen', sa.String(length=100), nullable=True))

def downgrade():
    op.drop_column('sales', 'id_origen')
    op.drop_column('sales', 'origen')
    op.drop_column('sales', 'comentario')
    op.drop_column('sales', 'tipo_venta')
    op.drop_column('sales', 'fiscal')
    op.drop_column('sales', 'total')
    op.drop_column('sales', 'medio_pago')
    op.drop_column('sales', 'camarero')
    op.drop_column('sales', 'personas')
    op.drop_column('sales', 'sala')
    op.drop_column('sales', 'mesa')
    op.drop_column('sales', 'cliente')
    op.drop_column('sales', 'estado')
    op.drop_column('sales', 'caja')
    op.drop_column('sales', 'cerrada')
    op.drop_column('sales', 'creacion')
    op.drop_index(op.f('ix_sales_fecha'), table_name='sales')
    op.drop_column('sales', 'fecha')
