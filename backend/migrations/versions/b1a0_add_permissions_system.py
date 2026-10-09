"""add permissions system (modules, role_permissions, user_permissions) with seed

Revision ID: b1a0_add_permissions_system
Revises: add_menu_tables
Create Date: 2026-10-08 00:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = 'b1a0_add_permissions_system'
down_revision = 'add_menu_tables'
branch_labels = None
depends_on = None

# (name, display_name, description, category, route)
MODULES = [
    ('Employees', 'Empleados', 'Gestión de empleados, puestos y documentación', 'HR', '/employees'),
    ('Schedules', 'Horarios', 'Horarios, turnos, horas trabajadas, feriados y licencias', 'HR', '/schedules'),
    ('Payroll', 'Sueldos', 'Liquidación de sueldos y reclamos', 'Finance', '/payroll'),
    ('Reports', 'Reportes', 'Reportes, análisis y predicciones', 'Analytics', '/reports'),
    ('Expenses', 'Gastos', 'Gastos y categorías de gastos', 'Finance', '/expenses'),
    ('Sales', 'Ventas', 'Historial e importación de ventas', 'Finance', '/sales'),
    ('Menu', 'Carta', 'Carta digital', 'Operations', '/menu'),
    ('Suppliers', 'Proveedores', 'Proveedores y sus gastos', 'Finance', '/suppliers'),
    ('Products', 'Productos', 'Productos, variantes, recetas y categorías', 'Operations', '/products'),
    ('Stock', 'Stock e insumos', 'Insumos y control de stock', 'Operations', '/stock'),
    ('MyPayroll', 'Mis Nóminas', 'Recibos de sueldo propios', 'Self-Service', '/my-payrolls'),
    ('MySchedule', 'Mi Horario', 'Horario, fichadas y ausencias propias', 'Self-Service', '/my-schedule'),
]
EMPLOYEE_MODULES = {'MyPayroll', 'MySchedule'}


def upgrade():
    modules = op.create_table(
        'modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=20), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('route', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_modules_name'), 'modules', ['name'], unique=True)

    role_permissions = op.create_table(
        'role_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('is_granted', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role', 'module_id', name='uq_role_module'),
    )
    op.create_index(op.f('ix_role_permissions_role'), 'role_permissions', ['role'], unique=False)

    op.create_table(
        'user_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('is_granted', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'module_id', name='uq_user_module'),
    )
    op.create_index(op.f('ix_user_permissions_user_id'), 'user_permissions', ['user_id'], unique=False)

    now = datetime.utcnow()
    op.bulk_insert(modules, [
        {'id': index, 'name': name, 'display_name': display, 'description': description,
         'icon': None, 'category': category, 'route': route, 'is_active': True,
         'created_at': now, 'updated_at': now}
        for index, (name, display, description, category, route) in enumerate(MODULES, start=1)
    ])
    rows = []
    for index, (name, *_rest) in enumerate(MODULES, start=1):
        rows.append({'role': 'admin', 'module_id': index, 'is_granted': True,
                     'created_at': now, 'updated_at': now})
        rows.append({'role': 'employee', 'module_id': index, 'is_granted': name in EMPLOYEE_MODULES,
                     'created_at': now, 'updated_at': now})
    op.bulk_insert(role_permissions, rows)

    # En PostgreSQL la secuencia del id no avanza con ids explícitos: ajustarla.
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("SELECT setval(pg_get_serial_sequence('modules', 'id'), (SELECT MAX(id) FROM modules))")


def downgrade():
    op.drop_index(op.f('ix_user_permissions_user_id'), table_name='user_permissions')
    op.drop_table('user_permissions')
    op.drop_index(op.f('ix_role_permissions_role'), table_name='role_permissions')
    op.drop_table('role_permissions')
    op.drop_index(op.f('ix_modules_name'), table_name='modules')
    op.drop_table('modules')
