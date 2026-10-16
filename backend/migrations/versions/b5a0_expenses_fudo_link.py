"""link expenses, suppliers and expense categories to Fudo; add fudo_sync_runs

Revision ID: b5a0_expenses_fudo_link
Revises: b4a0_add_fiscal_invoicing
Create Date: 2026-10-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b5a0_expenses_fudo_link'
down_revision = 'b4a0_add_fiscal_invoicing'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('suppliers') as batch:
        batch.add_column(sa.Column('fudo_provider_id', sa.String(50), nullable=True))
        batch.create_unique_constraint('uq_suppliers_fudo_provider_id', ['fudo_provider_id'])
    with op.batch_alter_table('expense_categories') as batch:
        batch.add_column(sa.Column('fudo_category_id', sa.String(50), nullable=True))
        batch.create_unique_constraint('uq_expense_categories_fudo_category_id', ['fudo_category_id'])
    with op.batch_alter_table('expenses') as batch:
        batch.add_column(sa.Column('source', sa.String(10), nullable=False, server_default='galia'))
        batch.add_column(sa.Column('category_overridden', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column('supplier_overridden', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute("UPDATE expenses SET source = 'fudo' WHERE external_id IS NOT NULL")
    op.create_table(
        'fudo_sync_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('params', sa.JSON(), nullable=True),
        sa.Column('stats', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('triggered_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )
    op.create_index('ix_fudo_sync_runs_kind_started_at', 'fudo_sync_runs', ['kind', 'started_at'])


def downgrade():
    op.drop_index('ix_fudo_sync_runs_kind_started_at', table_name='fudo_sync_runs')
    op.drop_table('fudo_sync_runs')
    with op.batch_alter_table('expenses') as batch:
        batch.drop_column('supplier_overridden')
        batch.drop_column('category_overridden')
        batch.drop_column('source')
    with op.batch_alter_table('expense_categories') as batch:
        batch.drop_constraint('uq_expense_categories_fudo_category_id', type_='unique')
        batch.drop_column('fudo_category_id')
    with op.batch_alter_table('suppliers') as batch:
        batch.drop_constraint('uq_suppliers_fudo_provider_id', type_='unique')
        batch.drop_column('fudo_provider_id')
