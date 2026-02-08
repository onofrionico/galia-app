import os
import sys
from datetime import datetime, timedelta, time
from decimal import Decimal
import random

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.employee import Employee
from app.models.job_position import JobPosition
from app.models.time_tracking import TimeTracking
from app.models.work_block import WorkBlock
from app.models.shift import Shift
from app.models.schedule import Schedule

def create_payroll_test_data():
    app = create_app('development')
    
    with app.app_context():
        print("🚀 Iniciando generación de datos de prueba para módulo de sueldos...")
        
        # Verificar si existe un admin
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            # Intentar obtener el usuario admin@galia.com
            admin = User.query.filter_by(email='admin@galia.com').first()
            if admin:
                # Actualizar a admin si existe pero no es admin
                if admin.role != 'admin':
                    admin.role = 'admin'
                    db.session.commit()
                    print("✅ Usuario existente actualizado a admin: admin@galia.com")
            else:
                print("❌ No se encontró un usuario administrador. Creando uno...")
                admin = User(
                    email='admin@galia.com',
                    role='admin',
                    is_active=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Usuario admin creado: admin@galia.com / admin123")
        else:
            print(f"✅ Usuario admin encontrado: {admin.email}")
        
        # Crear o obtener puestos de trabajo
        print("\n📋 Creando puestos de trabajo...")
        
        positions_data = [
            {
                'name': 'Barista',
                'description': 'Preparación de bebidas y atención al cliente',
                'contract_type': 'por_hora',
                'hourly_rate': Decimal('1500.00'),
                'standard_hours_per_week': 40,
                'standard_hours_per_month': 160
            },
            {
                'name': 'Cajero/a',
                'description': 'Manejo de caja y cobros',
                'contract_type': 'por_hora',
                'hourly_rate': Decimal('1400.00'),
                'standard_hours_per_week': 40,
                'standard_hours_per_month': 160
            },
            {
                'name': 'Cocinero/a',
                'description': 'Preparación de alimentos',
                'contract_type': 'por_hora',
                'hourly_rate': Decimal('1800.00'),
                'standard_hours_per_week': 40,
                'standard_hours_per_month': 160
            },
            {
                'name': 'Ayudante de Cocina',
                'description': 'Asistencia en cocina y limpieza',
                'contract_type': 'por_hora',
                'hourly_rate': Decimal('1200.00'),
                'standard_hours_per_week': 40,
                'standard_hours_per_month': 160
            }
        ]
        
        positions = {}
        for pos_data in positions_data:
            position = JobPosition.query.filter_by(name=pos_data['name']).first()
            if not position:
                position = JobPosition(
                    name=pos_data['name'],
                    description=pos_data['description'],
                    contract_type=pos_data['contract_type'],
                    hourly_rate=pos_data['hourly_rate'],
                    standard_hours_per_week=pos_data['standard_hours_per_week'],
                    standard_hours_per_month=pos_data['standard_hours_per_month'],
                    is_active=True,
                    created_by_id=admin.id
                )
                db.session.add(position)
                print(f"  ✅ Puesto creado: {pos_data['name']} - ${pos_data['hourly_rate']}/hora")
            positions[pos_data['name']] = position
        
        db.session.commit()
        
        # Crear empleados de prueba
        print("\n👥 Creando empleados de prueba...")
        
        employees_data = [
            {
                'first_name': 'María',
                'last_name': 'González',
                'dni': '35123456',
                'cuil': '27-35123456-8',
                'email': 'maria.gonzalez@galia.com',
                'position': 'Barista'
            },
            {
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'dni': '36234567',
                'cuil': '20-36234567-9',
                'email': 'juan.perez@galia.com',
                'position': 'Cajero/a'
            },
            {
                'first_name': 'Ana',
                'last_name': 'Martínez',
                'dni': '37345678',
                'cuil': '27-37345678-0',
                'email': 'ana.martinez@galia.com',
                'position': 'Cocinero/a'
            },
            {
                'first_name': 'Carlos',
                'last_name': 'López',
                'dni': '38456789',
                'cuil': '20-38456789-1',
                'email': 'carlos.lopez@galia.com',
                'position': 'Ayudante de Cocina'
            },
            {
                'first_name': 'Laura',
                'last_name': 'Fernández',
                'dni': '39567890',
                'cuil': '27-39567890-2',
                'email': 'laura.fernandez@galia.com',
                'position': 'Barista'
            }
        ]
        
        employees = []
        for emp_data in employees_data:
            # Verificar si el usuario ya existe
            user = User.query.filter_by(email=emp_data['email']).first()
            if not user:
                user = User(
                    email=emp_data['email'],
                    is_admin=False,
                    is_active=True
                )
                user.set_password('empleado123')
                db.session.add(user)
                db.session.flush()
            
            # Verificar si el empleado ya existe
            employee = Employee.query.filter_by(dni=emp_data['dni']).first()
            if not employee:
                employee = Employee(
                    user_id=user.id,
                    first_name=emp_data['first_name'],
                    last_name=emp_data['last_name'],
                    dni=emp_data['dni'],
                    cuil=emp_data['cuil'],
                    birth_date=datetime(1995, 1, 1).date(),
                    phone='1123456789',
                    address='Calle Falsa 123, CABA',
                    employment_relationship='dependencia',
                    emergency_contact_name='Contacto de Emergencia',
                    emergency_contact_phone='1198765432',
                    emergency_contact_relationship='Familiar',
                    hire_date=datetime(2024, 1, 1).date(),
                    status='activo',
                    current_job_position_id=positions[emp_data['position']].id,
                    created_by_id=admin.id
                )
                db.session.add(employee)
                print(f"  ✅ Empleado creado: {emp_data['first_name']} {emp_data['last_name']} - {emp_data['position']}")
            employees.append(employee)
        
        db.session.commit()
        
        # Generar registros de horas trabajadas para los últimos 3 meses
        print("\n⏰ Generando registros de horas trabajadas...")
        
        today = datetime.now().date()
        
        # Generar datos para los últimos 3 meses
        for month_offset in range(3):
            # Calcular el mes
            target_date = today - timedelta(days=30 * month_offset)
            year = target_date.year
            month = target_date.month
            
            # Primer y último día del mes
            first_day = datetime(year, month, 1).date()
            if month == 12:
                last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
            
            print(f"\n  📅 Generando datos para {first_day.strftime('%B %Y')}...")
            
            # Crear un schedule para el mes
            schedule = Schedule.query.filter(
                Schedule.start_date <= first_day,
                Schedule.end_date >= last_day
            ).first()
            
            if not schedule:
                schedule = Schedule(
                    start_date=first_day,
                    end_date=last_day,
                    status='published',
                    created_by=admin.id
                )
                db.session.add(schedule)
                db.session.flush()
            
            # Para cada empleado
            for employee in employees:
                days_worked = 0
                total_hours = 0
                
                # Generar registros para días laborables (lunes a sábado)
                current_date = first_day
                while current_date <= last_day:
                    # Solo días laborables (0=lunes, 6=domingo)
                    if current_date.weekday() < 6:  # Lunes a sábado
                        # 85% de probabilidad de trabajar ese día
                        if random.random() < 0.85:
                            # Verificar si ya existe el registro
                            existing = TimeTracking.query.filter_by(
                                employee_id=employee.id,
                                tracking_date=current_date
                            ).first()
                            
                            if not existing:
                                # Crear registro de tiempo
                                time_record = TimeTracking(
                                    employee_id=employee.id,
                                    tracking_date=current_date
                                )
                                db.session.add(time_record)
                                db.session.flush()
                                
                                # Generar 1-2 bloques de trabajo por día
                                num_blocks = random.choice([1, 1, 1, 2])  # Más probable 1 bloque
                                
                                if num_blocks == 1:
                                    # Un solo turno (ej: 9:00 - 17:00)
                                    start_hour = random.randint(8, 10)
                                    duration = random.randint(7, 9)  # 7-9 horas
                                    
                                    start_time = time(start_hour, 0)
                                    end_time = time(start_hour + duration, 0)
                                    
                                    block = WorkBlock(
                                        time_tracking_id=time_record.id,
                                        start_time=start_time,
                                        end_time=end_time
                                    )
                                    db.session.add(block)
                                    total_hours += duration
                                else:
                                    # Dos turnos (ej: 9:00-13:00 y 14:00-18:00)
                                    # Turno mañana
                                    start_time1 = time(9, 0)
                                    end_time1 = time(13, 0)
                                    block1 = WorkBlock(
                                        time_tracking_id=time_record.id,
                                        start_time=start_time1,
                                        end_time=end_time1
                                    )
                                    db.session.add(block1)
                                    
                                    # Turno tarde
                                    start_time2 = time(14, 0)
                                    end_time2 = time(18, 0)
                                    block2 = WorkBlock(
                                        time_tracking_id=time_record.id,
                                        start_time=start_time2,
                                        end_time=end_time2
                                    )
                                    db.session.add(block2)
                                    total_hours += 8
                                
                                days_worked += 1
                                
                                # Crear shift programado (grilla) - similar pero con pequeñas diferencias
                                shift_start = time(9, 0)
                                shift_end = time(17, 0)
                                shift_hours = 8
                                
                                existing_shift = Shift.query.filter_by(
                                    schedule_id=schedule.id,
                                    employee_id=employee.id,
                                    shift_date=current_date
                                ).first()
                                
                                if not existing_shift:
                                    shift = Shift(
                                        schedule_id=schedule.id,
                                        employee_id=employee.id,
                                        shift_date=current_date,
                                        start_time=shift_start,
                                        end_time=shift_end,
                                        hours=Decimal(str(shift_hours))
                                    )
                                    db.session.add(shift)
                    
                    current_date += timedelta(days=1)
                
                print(f"    ✅ {employee.full_name}: {days_worked} días trabajados, ~{total_hours} horas")
        
        db.session.commit()
        
        print("\n✅ Datos de prueba generados exitosamente!")
        print("\n📊 Resumen:")
        print(f"  - {len(employees)} empleados creados")
        print(f"  - {len(positions_data)} puestos de trabajo")
        print(f"  - Registros de horas para los últimos 3 meses")
        print(f"  - Turnos programados (grilla) para comparación")
        
        print("\n🔑 Credenciales:")
        print("  Admin: admin@galia.com / admin123")
        print("  Empleados: [email] / empleado123")
        
        print("\n💡 Ahora puedes:")
        print("  1. Ir al módulo de Sueldos")
        print("  2. Seleccionar un mes y empleado")
        print("  3. Generar nóminas y ver la comparación de horas")
        print("  4. Validar nóminas y generar PDFs")

if __name__ == '__main__':
    create_payroll_test_data()
