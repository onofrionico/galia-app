"""make employee fields optional

Revision ID: make_employee_fields_optional
Revises: 
Create Date: 2026-02-21 12:37:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'make_employee_fields_optional'
down_revision = None  # Will be set by alembic

def upgrade():
    # Make fields nullable except for required ones
    with op.batch_alter_table('employees', schema=None) as batch_op:
        batch_op.alter_column('cuil',
                              existing_type=sa.String(13),
                              nullable=True)
        batch_op.alter_column('birth_date',
                              existing_type=sa.Date(),
                              nullable=True)
        batch_op.alter_column('phone',
                              existing_type=sa.String(20),
                              nullable=True)
        batch_op.alter_column('address',
                              existing_type=sa.Text(),
                              nullable=True)
        batch_op.alter_column('employment_relationship',
                              existing_type=sa.String(20),
                              nullable=True)
        batch_op.alter_column('emergency_contact_name',
                              existing_type=sa.String(100),
                              nullable=True)
        batch_op.alter_column('emergency_contact_phone',
                              existing_type=sa.String(20),
                              nullable=True)
        batch_op.alter_column('emergency_contact_relationship',
                              existing_type=sa.String(50),
                              nullable=True)
        batch_op.alter_column('email',
                              existing_type=sa.String(120),
                              nullable=True)

def downgrade():
    # Revert fields to non-nullable
    with op.batch_alter_table('employees', schema=None) as batch_op:
        batch_op.alter_column('cuil',
                              existing_type=sa.String(13),
                              nullable=False)
        batch_op.alter_column('birth_date',
                              existing_type=sa.Date(),
                              nullable=False)
        batch_op.alter_column('phone',
                              existing_type=sa.String(20),
                              nullable=False)
        batch_op.alter_column('address',
                              existing_type=sa.Text(),
                              nullable=False)
        batch_op.alter_column('employment_relationship',
                              existing_type=sa.String(20),
                              nullable=False)
        batch_op.alter_column('emergency_contact_name',
                              existing_type=sa.String(100),
                              nullable=False)
        batch_op.alter_column('emergency_contact_phone',
                              existing_type=sa.String(20),
                              nullable=False)
        batch_op.alter_column('emergency_contact_relationship',
                              existing_type=sa.String(50),
                              nullable=False)
        batch_op.alter_column('email',
                              existing_type=sa.String(120),
                              nullable=False)
