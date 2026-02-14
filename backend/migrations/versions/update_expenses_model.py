"""Update expenses model to match CSV structure for external system import

Revision ID: update_expenses_model
Revises: 5f4b7f1abd00
Create Date: 2026-02-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_expenses_model'
down_revision = '5f4b7f1abd00'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old expenses table if it exists
    op.execute("DROP TABLE IF EXISTS expenses CASCADE")
    
    # Create new expenses table with updated structure
    op.create_table('expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.Integer(), nullable=True),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('fecha_vencimiento', sa.Date(), nullable=True),
        sa.Column('proveedor', sa.String(200), nullable=True),
        sa.Column('categoria', sa.String(100), nullable=True),
        sa.Column('subcategoria', sa.String(100), nullable=True),
        sa.Column('comentario', sa.Text(), nullable=True),
        sa.Column('estado_pago', sa.String(50), nullable=False, server_default='Pendiente'),
        sa.Column('importe', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('de_caja', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('caja', sa.String(100), nullable=True),
        sa.Column('medio_pago', sa.String(100), nullable=True),
        sa.Column('numero_fiscal', sa.String(100), nullable=True),
        sa.Column('tipo_comprobante', sa.String(100), nullable=True),
        sa.Column('numero_comprobante', sa.String(100), nullable=True),
        sa.Column('creado_por', sa.String(100), nullable=True),
        sa.Column('cancelado', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['category_id'], ['expense_categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_expenses_external_id', 'expenses', ['external_id'], unique=True)
    op.create_index('idx_expenses_fecha', 'expenses', ['fecha'])
    op.create_index('idx_expenses_proveedor', 'expenses', ['proveedor'])
    op.create_index('idx_expenses_categoria', 'expenses', ['categoria'])
    op.create_index('idx_expenses_estado_pago', 'expenses', ['estado_pago'])


def downgrade():
    op.drop_index('idx_expenses_estado_pago', table_name='expenses')
    op.drop_index('idx_expenses_categoria', table_name='expenses')
    op.drop_index('idx_expenses_proveedor', table_name='expenses')
    op.drop_index('idx_expenses_fecha', table_name='expenses')
    op.drop_index('idx_expenses_external_id', table_name='expenses')
    op.drop_table('expenses')
