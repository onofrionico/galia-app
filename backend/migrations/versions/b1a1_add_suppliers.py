"""add suppliers table and expenses.supplier_id

Revision ID: b1a1_add_suppliers
Revises: b1a0_add_permissions_system
Create Date: 2026-10-08 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b1a1_add_suppliers'
down_revision = 'b1a0_add_permissions_system'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('cuit', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_suppliers_cuit'), 'suppliers', ['cuit'], unique=True)

    with op.batch_alter_table('expenses') as batch:
        batch.add_column(sa.Column('supplier_id', sa.Integer(), nullable=True))
        batch.create_index(batch.f('ix_expenses_supplier_id'), ['supplier_id'], unique=False)
        batch.create_foreign_key('fk_expenses_supplier_id_suppliers', 'suppliers', ['supplier_id'], ['id'])


def downgrade():
    with op.batch_alter_table('expenses') as batch:
        batch.drop_constraint('fk_expenses_supplier_id_suppliers', type_='foreignkey')
        batch.drop_index(batch.f('ix_expenses_supplier_id'))
        batch.drop_column('supplier_id')
    op.drop_index(op.f('ix_suppliers_cuit'), table_name='suppliers')
    op.drop_table('suppliers')
