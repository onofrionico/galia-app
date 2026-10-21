"""sales.fecha = día comercial en Argentina (antes: día UTC del cierre)

Las ventas de la API de Fudo y del POS guardan `creacion`/`cerrada` en UTC y tomaban
`fecha` como el día UTC del cierre: una mesa cerrada a las 21:30 caía al día siguiente.
Se recalcula como el día en Argentina (UTC-3) con corte a las 6 de la mañana
(ver BUSINESS_DAY_CUTOFF_HOUR en app/utils/timezone_utils.py), o sea UTC - 9 horas.

Las filas importadas por CSV no se tocan: su fecha y horarios ya vienen en hora local.
Las de la API se reconocen porque fudo_sync guarda id_origen = external_id.

Revision ID: b5c0_sales_business_date
Revises: b5b0_add_mercadopago
Create Date: 2026-10-20 12:00:00.000000

"""
from alembic import op


revision = 'b5c0_sales_business_date'
down_revision = 'b5b0_add_mercadopago'
branch_labels = None
depends_on = None

UTC_ROWS = (
    "((origen = 'Fudo' AND id_origen = CAST(external_id AS VARCHAR)) "
    "OR (source = 'galia' AND origen = 'Galia POS')) "
    "AND COALESCE(cerrada, creacion) IS NOT NULL"
)


def upgrade():
    if op.get_bind().dialect.name != 'postgresql':
        return
    op.execute(
        "UPDATE sales SET fecha = CAST(COALESCE(cerrada, creacion) - INTERVAL '9 hours' AS DATE) "
        f"WHERE {UTC_ROWS}"
    )


def downgrade():
    if op.get_bind().dialect.name != 'postgresql':
        return
    op.execute(f"UPDATE sales SET fecha = CAST(COALESCE(cerrada, creacion) AS DATE) WHERE {UTC_ROWS}")
