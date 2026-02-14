"""Update sales model to match CSV structure

Revision ID: update_sales_model
Revises: add_time_tracking_model
Create Date: 2026-02-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_sales_model'
down_revision = 'add_time_tracking'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old tables if they exist
    op.execute("DROP TABLE IF EXISTS sale_items CASCADE")
    op.execute("DROP TABLE IF EXISTS sales CASCADE")
    
    # Create new sales table with updated structure
    op.create_table('sales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.Integer(), nullable=True),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('creacion', sa.DateTime(), nullable=False),
        sa.Column('cerrada', sa.DateTime(), nullable=True),
        sa.Column('caja', sa.String(100), nullable=True),
        sa.Column('estado', sa.String(50), nullable=False, server_default='En curso'),
        sa.Column('cliente', sa.String(200), nullable=True),
        sa.Column('mesa', sa.String(20), nullable=True),
        sa.Column('sala', sa.String(100), nullable=True),
        sa.Column('personas', sa.Integer(), nullable=True),
        sa.Column('camarero', sa.String(200), nullable=True),
        sa.Column('medio_pago', sa.String(100), nullable=True),
        sa.Column('total', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('fiscal', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tipo_venta', sa.String(50), nullable=False, server_default='Local'),
        sa.Column('comentario', sa.Text(), nullable=True),
        sa.Column('origen', sa.String(100), nullable=True),
        sa.Column('id_origen', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_sales_external_id', 'sales', ['external_id'], unique=True)
    op.create_index('idx_sales_fecha', 'sales', ['fecha'])
    op.create_index('idx_sales_estado', 'sales', ['estado'])
    op.create_index('idx_sales_tipo_venta', 'sales', ['tipo_venta'])
    op.create_index('idx_sales_origen', 'sales', ['origen'])


def downgrade():
    op.drop_index('idx_sales_origen', table_name='sales')
    op.drop_index('idx_sales_tipo_venta', table_name='sales')
    op.drop_index('idx_sales_estado', table_name='sales')
    op.drop_index('idx_sales_fecha', table_name='sales')
    op.drop_index('idx_sales_external_id', table_name='sales')
    op.drop_table('sales')
