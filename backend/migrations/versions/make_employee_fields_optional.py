"""make employee fields optional

Revision ID: make_employee_fields_optional
Revises: 
Create Date: 2026-02-21 12:37:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'make_employee_fields_optional'
down_revision = 'merge_expense_branches'

def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col['name']: col for col in inspector.get_columns('employees')}
    
    with op.batch_alter_table('employees', schema=None) as batch_op:
        if 'cuil' in columns and not columns['cuil']['nullable']:
            batch_op.alter_column('cuil',
                                  existing_type=sa.String(13),
                                  nullable=True)
        if 'birth_date' in columns and not columns['birth_date']['nullable']:
            batch_op.alter_column('birth_date',
                                  existing_type=sa.Date(),
                                  nullable=True)
        if 'phone' in columns and not columns['phone']['nullable']:
            batch_op.alter_column('phone',
                                  existing_type=sa.String(20),
                                  nullable=True)
        if 'address' in columns and not columns['address']['nullable']:
            batch_op.alter_column('address',
                                  existing_type=sa.Text(),
                                  nullable=True)
        if 'employment_relationship' in columns and not columns['employment_relationship']['nullable']:
            batch_op.alter_column('employment_relationship',
                                  existing_type=sa.String(20),
                                  nullable=True)
        if 'emergency_contact_name' in columns and not columns['emergency_contact_name']['nullable']:
            batch_op.alter_column('emergency_contact_name',
                                  existing_type=sa.String(100),
                                  nullable=True)
        if 'emergency_contact_phone' in columns and not columns['emergency_contact_phone']['nullable']:
            batch_op.alter_column('emergency_contact_phone',
                                  existing_type=sa.String(20),
                                  nullable=True)
        if 'emergency_contact_relationship' in columns and not columns['emergency_contact_relationship']['nullable']:
            batch_op.alter_column('emergency_contact_relationship',
                                  existing_type=sa.String(50),
                                  nullable=True)

def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col['name']: col for col in inspector.get_columns('employees')}
    
    with op.batch_alter_table('employees', schema=None) as batch_op:
        if 'cuil' in columns and columns['cuil']['nullable']:
            batch_op.alter_column('cuil',
                                  existing_type=sa.String(13),
                                  nullable=False)
        if 'birth_date' in columns and columns['birth_date']['nullable']:
            batch_op.alter_column('birth_date',
                                  existing_type=sa.Date(),
                                  nullable=False)
        if 'phone' in columns and columns['phone']['nullable']:
            batch_op.alter_column('phone',
                                  existing_type=sa.String(20),
                                  nullable=False)
        if 'address' in columns and columns['address']['nullable']:
            batch_op.alter_column('address',
                                  existing_type=sa.Text(),
                                  nullable=False)
        if 'employment_relationship' in columns and columns['employment_relationship']['nullable']:
            batch_op.alter_column('employment_relationship',
                                  existing_type=sa.String(20),
                                  nullable=False)
        if 'emergency_contact_name' in columns and columns['emergency_contact_name']['nullable']:
            batch_op.alter_column('emergency_contact_name',
                                  existing_type=sa.String(100),
                                  nullable=False)
        if 'emergency_contact_phone' in columns and columns['emergency_contact_phone']['nullable']:
            batch_op.alter_column('emergency_contact_phone',
                                  existing_type=sa.String(20),
                                  nullable=False)
        if 'emergency_contact_relationship' in columns and columns['emergency_contact_relationship']['nullable']:
            batch_op.alter_column('emergency_contact_relationship',
                                  existing_type=sa.String(50),
                                  nullable=False)
