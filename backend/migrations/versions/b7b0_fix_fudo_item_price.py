"""sale_items de Fudo: `price` era el total de la línea, no el unitario

La sync guardaba unit_price = price y total = price x cantidad, así que todo lo vendido
de a 2 o más unidades quedaba contado de más (en octubre de 2026 el reporte por producto
daba +25 % sobre las ventas). Se recalcula: total = price (lo que estaba en unit_price) y
unit_price = price / cantidad. Solo filas de Fudo (external_id no nulo); las del POS ya
estaban bien.

Antes de corregir copia sale_items completa en sale_items_backup_b7b0 (backup en la misma
base); el downgrade restaura los importes desde esa copia y la borra.

Revision ID: b7b0_fix_fudo_item_price
Revises: b7a1_drop_product_recipe_items
Create Date: 2026-11-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b7b0_fix_fudo_item_price'
down_revision = 'b7a1_drop_product_recipe_items'
branch_labels = None
depends_on = None

BACKUP = 'sale_items_backup_b7b0'
FUDO_ROWS = 'external_id IS NOT NULL AND quantity > 0'


def _has_backup():
    return sa.inspect(op.get_bind()).has_table(BACKUP)


def upgrade():
    if not _has_backup():
        op.execute(f'CREATE TABLE {BACKUP} AS SELECT * FROM sale_items')
    # En un UPDATE cada SET lee los valores anteriores de la fila.
    op.execute(f'UPDATE sale_items SET total = unit_price, unit_price = ROUND(unit_price / quantity, 2) '
               f'WHERE {FUDO_ROWS}')


def downgrade():
    if _has_backup():
        op.execute(f'UPDATE sale_items SET unit_price = b.unit_price, total = b.total '
                   f'FROM {BACKUP} b WHERE b.id = sale_items.id')
        op.drop_table(BACKUP)
    else:
        op.execute(f'UPDATE sale_items SET unit_price = total, total = ROUND(total * quantity, 2) WHERE {FUDO_ROWS}')
