"""add suppliers table and supplier_id to expenses

Revision ID: 4e00a6d26fe1
Revises: merge_heads_march8
Create Date: 2026-04-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e00a6d26fe1'
down_revision = 'merge_heads_march8'
branch_labels = None
depends_on = None


def upgrade():
    # Create suppliers table
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('cuit', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cuit'),
    )
    op.create_index(op.f('ix_suppliers_cuit'), 'suppliers', ['cuit'], unique=True)

    # Add supplier_id FK column to expenses
    op.add_column(
        'expenses',
        sa.Column('supplier_id', sa.Integer(), nullable=True)
    )
    op.create_index(op.f('ix_expenses_supplier_id'), 'expenses', ['supplier_id'], unique=False)
    op.create_foreign_key(
        'fk_expenses_supplier_id_suppliers',
        'expenses', 'suppliers',
        ['supplier_id'], ['id']
    )


def downgrade():
    op.drop_constraint('fk_expenses_supplier_id_suppliers', 'expenses', type_='foreignkey')
    op.drop_index(op.f('ix_expenses_supplier_id'), table_name='expenses')
    op.drop_column('expenses', 'supplier_id')

    op.drop_index(op.f('ix_suppliers_cuit'), table_name='suppliers')
    op.drop_table('suppliers')
