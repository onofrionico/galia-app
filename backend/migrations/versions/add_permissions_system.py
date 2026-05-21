"""Add permissions system - Module, RolePermission, UserPermission tables

Revision ID: add_permissions_system
Revises:
Create Date: 2026-05-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_permissions_system'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create Module table
    op.create_table('modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(20), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('route', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_modules_name'), 'modules', ['name'], unique=True)

    # Create RolePermission table
    op.create_table('role_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('is_granted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role', 'module_id', name='uq_role_module')
    )
    op.create_index(op.f('ix_role_permissions_role'), 'role_permissions', ['role'], unique=False)

    # Create UserPermission table
    op.create_table('user_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('is_granted', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'module_id', name='uq_user_module')
    )
    op.create_index(op.f('ix_user_permissions_user_id'), 'user_permissions', ['user_id'], unique=False)

    # Insert default modules
    modules = [
        ('Dashboard', 'Dashboard', 'Acceso al panel principal', '📊', 'Core', '/dashboard'),
        ('POS', 'Caja/POS', 'Sistema de punto de venta', '💳', 'Operations', '/pos'),
        ('Payroll', 'Nóminas', 'Gestión de nóminas y sueldos', '💰', 'Finance', '/payroll'),
        ('Schedules', 'Horarios', 'Gestión de horarios de trabajo', '📅', 'HR', '/schedules'),
        ('Employees', 'Empleados', 'Gestión de empleados', '👥', 'HR', '/employees'),
        ('Reports', 'Reportes', 'Reportes y análisis', '📈', 'Analytics', '/reports'),
        ('Expenses', 'Gastos', 'Gestión de gastos', '💸', 'Finance', '/expenses'),
        ('Supplies', 'Insumos', 'Gestión de insumos y stock', '📦', 'Operations', '/supplies'),
        ('Configuration', 'Configuración', 'Configuración del sistema', '⚙️', 'Admin', '/configuration'),
        ('MyPayroll', 'Mi Nómina', 'Mis recibos de sueldo', '📄', 'Self-Service', '/my-payrolls'),
        ('MySchedule', 'Mi Horario', 'Mi horario de trabajo', '🗓️', 'Self-Service', '/my-schedule'),
    ]

    for name, display_name, description, icon, category, route in modules:
        op.execute(
            f"INSERT INTO modules (name, display_name, description, icon, category, route, is_active, created_at, updated_at) "
            f"VALUES ('{name}', '{display_name}', '{description}', '{icon}', '{category}', '{route}', true, NOW(), NOW())"
        )

    # Get module IDs for seeding permissions
    # Insert admin role with all modules = true
    op.execute("""
        INSERT INTO role_permissions (role, module_id, is_granted, created_at, updated_at)
        SELECT 'admin', id, true, NOW(), NOW() FROM modules WHERE is_active = true
    """)

    # Insert employee role with limited modules
    op.execute("""
        INSERT INTO role_permissions (role, module_id, is_granted, created_at, updated_at)
        SELECT 'employee', id, CASE
            WHEN name IN ('Dashboard', 'MyPayroll', 'MySchedule') THEN true
            ELSE false
        END, NOW(), NOW()
        FROM modules WHERE is_active = true
    """)

    # Insert supervisor role (if used)
    op.execute("""
        INSERT INTO role_permissions (role, module_id, is_granted, created_at, updated_at)
        SELECT 'supervisor', id, CASE
            WHEN name IN ('Dashboard', 'Schedules', 'Employees', 'Reports') THEN true
            ELSE false
        END, NOW(), NOW()
        FROM modules WHERE is_active = true
    """)


def downgrade():
    op.drop_index(op.f('ix_user_permissions_user_id'), table_name='user_permissions')
    op.drop_table('user_permissions')
    op.drop_index(op.f('ix_role_permissions_role'), table_name='role_permissions')
    op.drop_table('role_permissions')
    op.drop_index(op.f('ix_modules_name'), table_name='modules')
    op.drop_table('modules')
