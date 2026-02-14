from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.employee import Employee
from datetime import date

app = create_app()

with app.app_context():
    admin = User(
        email='admin@galia.com',
        role='admin',
        is_active=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    
    employee = Employee(
        user_id=admin.id,
        first_name='Admin',
        last_name='Sistema',
        dni='00000000',
        cuil='20-00000000-0',
        birth_date=date(1990, 1, 1),
        phone='0000000000',
        address='Sistema',
        employment_relationship='dependencia',
        emergency_contact_name='N/A',
        emergency_contact_phone='0000000000',
        emergency_contact_relationship='N/A',
        hire_date=date.today(),
        status='activo'
    )
    db.session.add(employee)
    db.session.commit()
    
    print(f"✓ Usuario administrador creado exitosamente")
    print(f"  Email: {admin.email}")
    print(f"  Password: admin123")
    print(f"  IMPORTANTE: Cambiar la contraseña en producción")
