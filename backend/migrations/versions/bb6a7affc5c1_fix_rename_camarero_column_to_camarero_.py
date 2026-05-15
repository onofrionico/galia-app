"""fix: rename camarero column to camarero_nombre to avoid conflict with relationship

Revision ID: bb6a7affc5c1
Revises: 3c9d6e2f1a4b
Create Date: 2026-05-15 16:03:58.386170

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'bb6a7affc5c1'
down_revision = '3c9d6e2f1a4b'
branch_labels = None
depends_on = None


def upgrade():
    # Rename camarero column to camarero_nombre to avoid conflict with relationship
    with op.batch_alter_table('sales', schema=None) as batch_op:
        batch_op.add_column(sa.Column('camarero_nombre', sa.String(length=200), nullable=True))
        # Copy data from old column to new column before dropping

    # Update all values from camarero to camarero_nombre
    op.execute('UPDATE sales SET camarero_nombre = camarero WHERE camarero IS NOT NULL')

    # Drop the old column
    with op.batch_alter_table('sales', schema=None) as batch_op:
        batch_op.drop_column('camarero')


def downgrade():
    # Revert the column rename
    with op.batch_alter_table('sales', schema=None) as batch_op:
        batch_op.add_column(sa.Column('camarero', sa.VARCHAR(length=200), autoincrement=False, nullable=True))

    # Copy data back from new column to old column
    op.execute('UPDATE sales SET camarero = camarero_nombre WHERE camarero_nombre IS NOT NULL')

    # Drop the new column
    with op.batch_alter_table('sales', schema=None) as batch_op:
        batch_op.drop_column('camarero_nombre')
