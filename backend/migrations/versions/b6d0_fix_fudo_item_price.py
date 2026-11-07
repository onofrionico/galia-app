"""sale_items de Fudo: `price` era el total de la línea, no el unitario

La sync guardaba unit_price = price y total = price x cantidad, así que todo lo vendido
de a 2 o más unidades quedaba contado de más (en octubre de 2026 el reporte por producto
daba +25 % sobre las ventas). Se recalcula: total = price (lo que estaba en unit_price) y
unit_price = price / cantidad. Solo filas de Fudo (external_id no nulo); las del POS ya
estaban bien.

Revision ID: b6d0_fix_fudo_item_price
Revises: b6c0_printer_chars_per_line
Create Date: 2026-10-24 12:00:00.000000

"""
from alembic import op


revision = 'b6d0_fix_fudo_item_price'
down_revision = 'b6c0_printer_chars_per_line'
branch_labels = None
depends_on = None

FUDO_ROWS = 'external_id IS NOT NULL AND quantity > 0'


def upgrade():
    # En un UPDATE cada SET lee los valores anteriores de la fila.
    op.execute(f'UPDATE sale_items SET total = unit_price, unit_price = ROUND(unit_price / quantity, 2) '
               f'WHERE {FUDO_ROWS}')


def downgrade():
    op.execute(f'UPDATE sale_items SET unit_price = total, total = ROUND(total * quantity, 2) WHERE {FUDO_ROWS}')
