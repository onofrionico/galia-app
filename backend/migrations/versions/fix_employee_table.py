"""fix employee table structure

Revision ID: fix_employee_table
Revises: b020c4aff4de
Create Date: 2026-02-05 18:26:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_employee_table'
down_revision = 'b020c4aff4de'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla employee_job_history si no existe
    op.execute("""
        CREATE TABLE IF NOT EXISTS employee_job_history (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            job_position_id INTEGER NOT NULL REFERENCES job_positions(id),
            start_date DATE NOT NULL,
            end_date DATE,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            CONSTRAINT fk_employee FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
            CONSTRAINT fk_job_position FOREIGN KEY (job_position_id) REFERENCES job_positions(id)
        )
    """)
    
    # Agregar columnas nuevas a employees
    op.add_column('employees', sa.Column('first_name', sa.String(100), nullable=True))
    op.add_column('employees', sa.Column('last_name', sa.String(100), nullable=True))
    op.add_column('employees', sa.Column('dni', sa.String(8), nullable=True))
    op.add_column('employees', sa.Column('cuil', sa.String(13), nullable=True))
    op.add_column('employees', sa.Column('birth_date', sa.Date(), nullable=True))
    op.add_column('employees', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('employees', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('employees', sa.Column('profile_photo_url', sa.Text(), nullable=True))
    op.add_column('employees', sa.Column('employment_relationship', sa.String(20), nullable=True))
    op.add_column('employees', sa.Column('emergency_contact_name', sa.String(100), nullable=True))
    op.add_column('employees', sa.Column('emergency_contact_phone', sa.String(20), nullable=True))
    op.add_column('employees', sa.Column('emergency_contact_relationship', sa.String(50), nullable=True))
    op.add_column('employees', sa.Column('status', sa.String(20), nullable=True))
    op.add_column('employees', sa.Column('current_job_position_id', sa.Integer(), nullable=True))
    op.add_column('employees', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('employees', sa.Column('created_by_id', sa.Integer(), nullable=True))
    op.add_column('employees', sa.Column('updated_by_id', sa.Integer(), nullable=True))
    
    # Migrar datos de full_name a first_name y last_name
    op.execute("""
        UPDATE employees 
        SET first_name = SPLIT_PART(full_name, ' ', 1),
            last_name = CASE 
                WHEN full_name LIKE '% %' THEN SUBSTRING(full_name FROM POSITION(' ' IN full_name) + 1)
                ELSE ''
            END,
            status = 'activo',
            updated_at = NOW()
        WHERE full_name IS NOT NULL
    """)
    
    # Hacer las columnas NOT NULL después de migrar los datos
    op.alter_column('employees', 'first_name', nullable=False)
    op.alter_column('employees', 'last_name', nullable=False)
    op.alter_column('employees', 'status', nullable=False)
    op.alter_column('employees', 'updated_at', nullable=False)
    
    # Crear foreign keys
    op.create_foreign_key('fk_employees_job_position', 'employees', 'job_positions', ['current_job_position_id'], ['id'])
    op.create_foreign_key('fk_employees_created_by', 'employees', 'users', ['created_by_id'], ['id'])
    op.create_foreign_key('fk_employees_updated_by', 'employees', 'users', ['updated_by_id'], ['id'])
    
    # Crear índices
    op.create_index('ix_employees_dni', 'employees', ['dni'], unique=True)
    op.create_index('ix_employees_cuil', 'employees', ['cuil'], unique=True)
    op.create_index('ix_employees_status', 'employees', ['status'])
    
    # Eliminar columnas antiguas
    op.drop_column('employees', 'full_name')
    op.drop_column('employees', 'hourly_rate')


def downgrade():
    # Restaurar columnas antiguas
    op.add_column('employees', sa.Column('full_name', sa.String(200), nullable=True))
    op.add_column('employees', sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True))
    
    # Migrar datos de vuelta
    op.execute("""
        UPDATE employees 
        SET full_name = first_name || ' ' || last_name
        WHERE first_name IS NOT NULL
    """)
    
    # Eliminar índices
    op.drop_index('ix_employees_status', 'employees')
    op.drop_index('ix_employees_cuil', 'employees')
    op.drop_index('ix_employees_dni', 'employees')
    
    # Eliminar foreign keys
    op.drop_constraint('fk_employees_updated_by', 'employees', type_='foreignkey')
    op.drop_constraint('fk_employees_created_by', 'employees', type_='foreignkey')
    op.drop_constraint('fk_employees_job_position', 'employees', type_='foreignkey')
    
    # Eliminar columnas nuevas
    op.drop_column('employees', 'updated_by_id')
    op.drop_column('employees', 'created_by_id')
    op.drop_column('employees', 'updated_at')
    op.drop_column('employees', 'current_job_position_id')
    op.drop_column('employees', 'status')
    op.drop_column('employees', 'emergency_contact_relationship')
    op.drop_column('employees', 'emergency_contact_phone')
    op.drop_column('employees', 'emergency_contact_name')
    op.drop_column('employees', 'employment_relationship')
    op.drop_column('employees', 'profile_photo_url')
    op.drop_column('employees', 'address')
    op.drop_column('employees', 'phone')
    op.drop_column('employees', 'birth_date')
    op.drop_column('employees', 'cuil')
    op.drop_column('employees', 'dni')
    op.drop_column('employees', 'last_name')
    op.drop_column('employees', 'first_name')
    
    # Eliminar tabla employee_job_history
    op.drop_table('employee_job_history')
