"""fix: backfill status field from legacy estado for backward compatibility

Revision ID: 9fbcd56354fa
Revises: bb6a7affc5c1
Create Date: 2026-05-15 16:06:35.759278

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9fbcd56354fa'
down_revision = 'bb6a7affc5c1'
branch_labels = None
depends_on = None


def upgrade():
    # Backfill status field from legacy estado values
    # Map: 'En curso' -> 'abierta', 'Cerrada' -> 'cerrada', others -> 'abierta' (default)
    op.execute("""
        UPDATE sales
        SET status = CASE
            WHEN estado = 'En curso' THEN 'abierta'
            WHEN estado = 'Cerrada' THEN 'cerrada'
            ELSE 'abierta'
        END
        WHERE status IS NULL OR status = 'abierta'
    """)


def downgrade():
    # Reset status back to default 'abierta' - data cannot be reliably reverted
    # as the original estado values may have changed
    op.execute("""
        UPDATE sales
        SET status = 'abierta'
    """)
