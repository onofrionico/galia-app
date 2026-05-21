import os
from app import create_app
from app.extensions import db
from app.models import Module, RolePermission

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

with app.app_context():
    # Check if modules exist
    modules_count = Module.query.count()
    print(f"📊 Módulos en la base de datos: {modules_count}")

    if modules_count == 0:
        print("\n❌ No hay módulos creados. Creando módulos...")

        modules_data = [
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

        for name, display_name, description, icon, category, route in modules_data:
            module = Module(
                name=name,
                display_name=display_name,
                description=description,
                icon=icon,
                category=category,
                route=route,
                is_active=True
            )
            db.session.add(module)
            print(f"  ✓ Módulo creado: {name}")

        db.session.commit()
        print("\n✅ Módulos creados exitosamente")

        # Create role permissions for admin
        print("\n📋 Creando permisos para roles...")
        modules = Module.query.all()

        # Admin has all permissions
        for module in modules:
            admin_perm = RolePermission(
                role='admin',
                module_id=module.id,
                is_granted=True
            )
            db.session.add(admin_perm)

        # Employee has limited permissions
        employee_modules = ['Dashboard', 'MyPayroll', 'MySchedule']
        for module in modules:
            employee_perm = RolePermission(
                role='employee',
                module_id=module.id,
                is_granted=module.name in employee_modules
            )
            db.session.add(employee_perm)

        # Supervisor permissions
        supervisor_modules = ['Dashboard', 'Schedules', 'Employees', 'Reports']
        for module in modules:
            supervisor_perm = RolePermission(
                role='supervisor',
                module_id=module.id,
                is_granted=module.name in supervisor_modules
            )
            db.session.add(supervisor_perm)

        db.session.commit()
        print("✅ Permisos de roles creados exitosamente\n")
    else:
        print(f"✓ Módulos ya existen:\n")
        for module in Module.query.all():
            print(f"  • {module.name}: {module.display_name}")

        # Check role permissions
        print(f"\n📋 Verificando permisos de roles...")
        for role in ['admin', 'employee', 'supervisor']:
            role_perms = RolePermission.query.filter_by(role=role).count()
            print(f"  • {role}: {role_perms} permisos")
