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
        full_name='Administrador',
        hourly_rate=0,
        hire_date=date.today()
    )
    db.session.add(employee)
    db.session.commit()
    
    print(f"✓ Usuario administrador creado exitosamente")
    print(f"  Email: {admin.email}")
    print(f"  Password: admin123")
    print(f"  IMPORTANTE: Cambiar la contraseña en producción")
