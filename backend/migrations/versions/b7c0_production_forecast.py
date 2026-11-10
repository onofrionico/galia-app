"""pronóstico de producción: turnos del día, configuración y componentes de productos

Tablas nuevas, no toca las existentes. Idempotente: crea cada tabla solo si falta y carga los
turnos iniciales (Desayuno 8-12, Almuerzo 12-16, Merienda 16-20) solo si la tabla está vacía.

Revision ID: b7c0_production_forecast
Revises: b7b0_fix_fudo_item_price
Create Date: 2026-11-10 12:00:00.000000

"""
from datetime import time

from alembic import op
import sqlalchemy as sa


revision = 'b7c0_production_forecast'
down_revision = 'b7b0_fix_fudo_item_price'
branch_labels = None
depends_on = None

INITIAL_DAY_PARTS = [('Desayuno', time(8), time(12)), ('Almuerzo', time(12), time(16)),
                     ('Merienda', time(16), time(20))]


def _has(name):
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade():
    if not _has('sales_day_parts'):
        op.create_table(
            'sales_day_parts',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('name', sa.String(50), nullable=False),
            sa.Column('start_time', sa.Time(), nullable=False),
            sa.Column('end_time', sa.Time(), nullable=False),
            sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        )
    if not _has('production_settings'):
        op.create_table(
            'production_settings',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('comparable_weeks', sa.Integer(), nullable=False, server_default='4'),
            sa.Column('holiday_window_months', sa.Integer(), nullable=False, server_default='12'),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        )
    if not _has('product_components'):
        op.create_table(
            'product_components',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('variant_id', sa.Integer(), sa.ForeignKey('product_variants.id'), nullable=False),
            sa.Column('component_variant_id', sa.Integer(), sa.ForeignKey('product_variants.id'), nullable=False),
            sa.Column('quantity', sa.Numeric(10, 3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.UniqueConstraint('variant_id', 'component_variant_id', name='uq_product_component'),
        )
        op.create_index('ix_product_components_variant_id', 'product_components', ['variant_id'])

    bind = op.get_bind()
    if not bind.execute(sa.text('SELECT COUNT(*) FROM sales_day_parts')).scalar():
        for position, (name, start, end) in enumerate(INITIAL_DAY_PARTS):
            bind.execute(sa.text('INSERT INTO sales_day_parts (name, start_time, end_time, position, is_active) '
                                 'VALUES (:n, :s, :e, :p, TRUE)'), {'n': name, 's': start, 'e': end, 'p': position})
    if not bind.execute(sa.text('SELECT COUNT(*) FROM production_settings WHERE id = 1')).scalar():
        bind.execute(sa.text('INSERT INTO production_settings (id, comparable_weeks, holiday_window_months) '
                             'VALUES (1, 4, 12)'))


def downgrade():
    for name in ('product_components', 'production_settings', 'sales_day_parts'):
        if _has(name):
            op.drop_table(name)
