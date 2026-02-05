from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.job_position import JobPosition
from datetime import datetime

app = create_app()

with app.app_context():
    print("Inicializando datos de prueba...")
    
    # Verificar si ya existe un admin
    admin = User.query.filter_by(email='admin@cafeteria.com').first()
    if not admin:
        print("Creando usuario administrador...")
        admin = User(
            email='admin@cafeteria.com',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✓ Usuario admin creado (email: admin@cafeteria.com, password: admin123)")
    else:
        print("✓ Usuario admin ya existe")
    
    # Crear puestos de trabajo si no existen
    positions_data = [
        {
            'name': 'Barista',
            'description': 'Preparación de cafés, bebidas calientes y frías',
            'contract_type': 'por_hora',
            'hourly_rate': 2500.00,
            'overtime_rate_multiplier': 1.5,
            'weekend_rate_multiplier': 1.25,
            'holiday_rate_multiplier': 2.0
        },
        {
            'name': 'Cajero/a',
            'description': 'Atención al cliente, cobros y manejo de caja',
            'contract_type': 'por_hora',
            'hourly_rate': 2300.00,
            'overtime_rate_multiplier': 1.5,
            'weekend_rate_multiplier': 1.25,
            'holiday_rate_multiplier': 2.0
        },
        {
            'name': 'Encargado/a',
            'description': 'Gestión general del local, supervisión de personal',
            'contract_type': 'full_time',
            'base_salary': 500000.00,
            'standard_hours_per_week': 40,
            'standard_hours_per_month': 160,
            'overtime_rate_multiplier': 1.5,
            'weekend_rate_multiplier': 1.25,
            'holiday_rate_multiplier': 2.0
        },
        {
            'name': 'Ayudante de Cocina',
            'description': 'Preparación de alimentos, limpieza y organización',
            'contract_type': 'part_time',
            'base_salary': 250000.00,
            'standard_hours_per_week': 20,
            'standard_hours_per_month': 80,
            'overtime_rate_multiplier': 1.5,
            'weekend_rate_multiplier': 1.25,
            'holiday_rate_multiplier': 2.0
        }
    ]
    
    created_count = 0
    for pos_data in positions_data:
        existing = JobPosition.query.filter_by(name=pos_data['name']).first()
        if not existing:
            position = JobPosition(**pos_data, is_active=True)
            db.session.add(position)
            created_count += 1
            print(f"✓ Puesto '{pos_data['name']}' creado")
        else:
            print(f"✓ Puesto '{pos_data['name']}' ya existe")
    
    if created_count > 0:
        db.session.commit()
        print(f"\n✓ {created_count} puestos de trabajo creados exitosamente")
    else:
        print("\n✓ Todos los puestos ya existían")
    
    # Mostrar resumen
    total_positions = JobPosition.query.count()
    total_users = User.query.count()
    
    print("\n" + "="*50)
    print("RESUMEN DE DATOS")
    print("="*50)
    print(f"Total de usuarios: {total_users}")
    print(f"Total de puestos de trabajo: {total_positions}")
    print("\nCredenciales de acceso:")
    print("  Email: admin@cafeteria.com")
    print("  Password: admin123")
    print("\nPuedes acceder a la aplicación en: http://localhost:5173")
    print("="*50)
