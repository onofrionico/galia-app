from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.employee import Employee
from datetime import date

app = create_app()

with app.app_context():
    # Crear usuario empleado
    emp_user = User(
        email='empleado@galia.com',
        role='employee',
        is_active=True
    )
    emp_user.set_password('empleado123')
    db.session.add(emp_user)
    db.session.commit()
    
    # Crear empleado asociado
    employee = Employee(
        user_id=emp_user.id,
        full_name='Juan Pérez',
        hourly_rate=2500,
        hire_date=date(2024, 1, 1)
    )
    db.session.add(employee)
    
    # Crear otro empleado
    emp_user2 = User(
        email='maria@galia.com',
        role='employee',
        is_active=True
    )
    emp_user2.set_password('maria123')
    db.session.add(emp_user2)
    db.session.commit()
    
    employee2 = Employee(
        user_id=emp_user2.id,
        full_name='María García',
        hourly_rate=2800,
        hire_date=date(2024, 2, 1)
    )
    db.session.add(employee2)
    
    db.session.commit()
    
    print("✓ Empleados de prueba creados exitosamente")
    print(f"  - {employee.full_name} (email: empleado@galia.com, password: empleado123)")
    print(f"  - {employee2.full_name} (email: maria@galia.com, password: maria123)")
