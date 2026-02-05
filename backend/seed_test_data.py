#!/usr/bin/env python3
"""
Script para cargar datos de prueba en la base de datos.
Este script NO es una migración, es un script independiente solo para desarrollo.

Uso:
    python seed_test_data.py

IMPORTANTE: Solo usar en desarrollo local, NO en producción.
"""

import sys
import os
from datetime import datetime, date, time, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.user import User
from app.models.employee import Employee
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.sale import Sale, SaleItem
from app.models.expense import Expense, ExpenseCategory
from app.models.supply import Supply, SupplyPrice
from app.models.payroll import Payroll
from app.models.notification import Notification, ScheduleChangeLog

def seed_data():
    """Inserta datos de prueba en la base de datos"""
    app = create_app()
    
    with app.app_context():
        # Verificar si ya existen datos
        existing_admin = User.query.filter_by(email='admin@galia.com').first()
        if existing_admin:
            print("⚠️  Ya existen datos de prueba en la base de datos.")
            response = input("¿Deseas eliminar todos los datos existentes y recargar? (s/N): ")
            if response.lower() != 's':
                print("❌ Operación cancelada.")
                return
            
            print("🗑️  Eliminando datos existentes...")
            # Eliminar en orden inverso para respetar foreign keys
            ScheduleChangeLog.query.delete()
            Notification.query.delete()
            Payroll.query.delete()
            SaleItem.query.delete()
            Sale.query.delete()
            Shift.query.delete()
            Schedule.query.delete()
            Expense.query.delete()
            SupplyPrice.query.delete()
            Supply.query.delete()
            ExpenseCategory.query.delete()
            Employee.query.delete()
            User.query.delete()
            db.session.commit()
            print("✅ Datos eliminados.")
        
        print("\n📝 Insertando datos de prueba...")
        
        # 1. USUARIOS
        print("   - Creando usuarios...")
        users = []
        
        admin = User(email='admin@galia.com', role='admin', is_active=True)
        admin.set_password('admin123')
        users.append(admin)
        
        employee_data = [
            ('juan.perez@galia.com', 'Juan Pérez', 1800.00, date(2024, 3, 15)),
            ('maria.garcia@galia.com', 'María García', 1900.00, date(2024, 2, 1)),
            ('carlos.rodriguez@galia.com', 'Carlos Rodríguez', 1750.00, date(2024, 4, 10)),
            ('ana.martinez@galia.com', 'Ana Martínez', 2000.00, date(2024, 1, 20)),
            ('pedro.lopez@galia.com', 'Pedro López', 1850.00, date(2024, 5, 5))
        ]
        
        for email, name, rate, hire_date in employee_data:
            user = User(email=email, role='employee', is_active=True)
            user.set_password('empleado123')
            users.append(user)
        
        db.session.add_all(users)
        db.session.commit()
        
        # 2. EMPLEADOS
        print("   - Creando empleados...")
        employees = []
        
        admin_employee = Employee(
            user_id=admin.id,
            full_name='Administrador Galia',
            hourly_rate=2500.00,
            hire_date=date(2024, 1, 1)
        )
        employees.append(admin_employee)
        
        for i, (email, name, rate, hire_date) in enumerate(employee_data, start=2):
            user = User.query.filter_by(email=email).first()
            employee = Employee(
                user_id=user.id,
                full_name=name,
                hourly_rate=rate,
                hire_date=hire_date
            )
            employees.append(employee)
        
        db.session.add_all(employees)
        db.session.commit()
        
        # 3. CATEGORÍAS DE GASTOS
        print("   - Creando categorías de gastos...")
        categories = [
            ExpenseCategory(name='Alimentos', description='Compra de ingredientes y alimentos', is_active=True),
            ExpenseCategory(name='Servicios', description='Luz, agua, gas, internet', is_active=True),
            ExpenseCategory(name='Mantenimiento', description='Reparaciones y mantenimiento', is_active=True),
            ExpenseCategory(name='Limpieza', description='Productos de limpieza', is_active=True),
            ExpenseCategory(name='Equipamiento', description='Compra de equipos y utensilios', is_active=True),
            ExpenseCategory(name='Marketing', description='Publicidad y promoción', is_active=True)
        ]
        db.session.add_all(categories)
        db.session.commit()
        
        # 4. SUMINISTROS
        print("   - Creando suministros...")
        supplies = [
            Supply(name='Café en grano', unit='kg', is_active=True),
            Supply(name='Leche', unit='litros', is_active=True),
            Supply(name='Azúcar', unit='kg', is_active=True),
            Supply(name='Vasos descartables', unit='unidades', is_active=True),
            Supply(name='Servilletas', unit='paquetes', is_active=True),
            Supply(name='Pan', unit='kg', is_active=True),
            Supply(name='Medialunas', unit='docenas', is_active=True),
            Supply(name='Facturas', unit='docenas', is_active=True)
        ]
        db.session.add_all(supplies)
        db.session.commit()
        
        # 5. PRECIOS DE SUMINISTROS
        print("   - Creando precios de suministros...")
        base_date = date.today() - timedelta(days=30)
        supply_prices = []
        
        # Café en grano
        for i in range(0, 31, 7):
            supply_prices.append(SupplyPrice(
                supply_id=supplies[0].id,
                price=8500.00 + (i * 50),
                recorded_at=base_date + timedelta(days=i),
                supplier='Café Premium SA',
                notes='Café colombiano',
                created_by=admin.id
            ))
        
        # Leche
        for i in range(0, 31, 3):
            supply_prices.append(SupplyPrice(
                supply_id=supplies[1].id,
                price=450.00 + (i * 5),
                recorded_at=base_date + timedelta(days=i),
                supplier='Lácteos del Sur',
                created_by=admin.id
            ))
        
        db.session.add_all(supply_prices)
        db.session.commit()
        
        # 6. GASTOS
        print("   - Creando gastos...")
        expenses = []
        for i in range(30):
            expense_date = base_date + timedelta(days=i)
            
            if i % 3 == 0:
                expenses.append(Expense(
                    amount=15000.00 + (i * 100),
                    expense_date=expense_date,
                    category_id=categories[0].id,
                    description=f'Compra de ingredientes para cafetería - {expense_date.strftime("%d/%m/%Y")}',
                    supplier='Mercado Central',
                    created_by=admin.id
                ))
            
            if i % 10 == 0:
                expenses.append(Expense(
                    amount=8500.00,
                    expense_date=expense_date,
                    category_id=categories[1].id,
                    description='Pago de servicios',
                    supplier='Varios',
                    created_by=admin.id
                ))
        
        db.session.add_all(expenses)
        db.session.commit()
        
        # 7. HORARIOS
        print("   - Creando horarios y turnos...")
        schedules = []
        for week in range(4):
            start_date = date.today() - timedelta(days=28) + timedelta(weeks=week)
            end_date = start_date + timedelta(days=6)
            
            schedule = Schedule(
                start_date=start_date,
                end_date=end_date,
                status='published' if week < 3 else 'draft',
                created_by=admin.id
            )
            schedules.append(schedule)
        
        db.session.add_all(schedules)
        db.session.commit()
        
        # 8. TURNOS
        shifts = []
        for schedule in schedules:
            for day in range(7):
                shift_date = schedule.start_date + timedelta(days=day)
                
                # Turno mañana
                shifts.append(Shift(
                    schedule_id=schedule.id,
                    employee_id=employees[1].id,
                    shift_date=shift_date,
                    start_time=time(7, 0),
                    end_time=time(15, 0),
                    hours=8.0
                ))
                
                shifts.append(Shift(
                    schedule_id=schedule.id,
                    employee_id=employees[2].id,
                    shift_date=shift_date,
                    start_time=time(8, 0),
                    end_time=time(16, 0),
                    hours=8.0
                ))
                
                # Turno tarde
                shifts.append(Shift(
                    schedule_id=schedule.id,
                    employee_id=employees[3].id,
                    shift_date=shift_date,
                    start_time=time(15, 0),
                    end_time=time(23, 0),
                    hours=8.0
                ))
                
                shifts.append(Shift(
                    schedule_id=schedule.id,
                    employee_id=employees[4].id,
                    shift_date=shift_date,
                    start_time=time(16, 0),
                    end_time=time(22, 0),
                    hours=6.0
                ))
                
                # Fin de semana
                if day >= 5:
                    shifts.append(Shift(
                        schedule_id=schedule.id,
                        employee_id=employees[5].id,
                        shift_date=shift_date,
                        start_time=time(9, 0),
                        end_time=time(17, 0),
                        hours=8.0
                    ))
        
        db.session.add_all(shifts)
        db.session.commit()
        
        # 9. VENTAS
        print("   - Creando ventas...")
        products = [
            {'desc': 'Café expreso', 'price': 800},
            {'desc': 'Café con leche', 'price': 1000},
            {'desc': 'Cappuccino', 'price': 1200},
            {'desc': 'Medialunas (3 unidades)', 'price': 1500},
            {'desc': 'Tostado', 'price': 2000},
            {'desc': 'Sandwich de miga', 'price': 1800},
            {'desc': 'Jugo natural', 'price': 1300},
            {'desc': 'Agua mineral', 'price': 600}
        ]
        
        sales = []
        sale_items = []
        
        for i in range(30):
            sale_date = base_date + timedelta(days=i)
            num_sales = 5 + (i % 6)
            
            for sale_num in range(num_sales):
                employee_id = employees[1 + (sale_num % 5)].id
                sale_hour = 7 + (sale_num * 2) % 15
                sale_time_obj = datetime.combine(sale_date, time(sale_hour, (sale_num * 15) % 60))
                
                payment_methods = ['efectivo', 'tarjeta_debito', 'tarjeta_credito', 'transferencia']
                payment_method = payment_methods[sale_num % 4]
                
                total_amount = 0
                num_items = 1 + (sale_num % 4)
                
                sale = Sale(
                    amount=0,
                    payment_method=payment_method,
                    employee_id=employee_id,
                    notes=f'Venta {sale_num + 1} del día' if sale_num % 3 == 0 else None,
                    created_at=sale_time_obj
                )
                sales.append(sale)
                db.session.add(sale)
                db.session.flush()
                
                for item_num in range(num_items):
                    product = products[(sale_num + item_num) % len(products)]
                    quantity = 1 + (item_num % 2)
                    unit_price = product['price']
                    subtotal = quantity * unit_price
                    total_amount += subtotal
                    
                    item = SaleItem(
                        sale_id=sale.id,
                        description=product['desc'],
                        quantity=quantity,
                        unit_price=unit_price,
                        subtotal=subtotal
                    )
                    sale_items.append(item)
                
                sale.amount = total_amount
        
        db.session.add_all(sale_items)
        db.session.commit()
        
        # 10. NÓMINAS
        print("   - Creando nóminas...")
        current_date = date.today()
        last_month = current_date.month - 1 if current_date.month > 1 else 12
        last_year = current_date.year if current_date.month > 1 else current_date.year - 1
        
        payrolls = []
        for i, employee in enumerate(employees[1:], start=1):
            hours_worked = 160.0 + (i * 5)
            gross_salary = hours_worked * float(employee.hourly_rate)
            
            payroll = Payroll(
                employee_id=employee.id,
                month=last_month,
                year=last_year,
                hours_worked=hours_worked,
                hourly_rate=employee.hourly_rate,
                gross_salary=gross_salary,
                generated_by=admin.id
            )
            payrolls.append(payroll)
        
        db.session.add_all(payrolls)
        db.session.commit()
        
        # 11. NOTIFICACIONES
        print("   - Creando notificaciones...")
        notifications = [
            Notification(
                user_id=users[1].id,
                title='Nuevo horario publicado',
                message=f'Se ha publicado el horario de la semana del {(date.today() - timedelta(days=7)).strftime("%d/%m/%Y")}',
                type='schedule_change',
                is_read=True,
                related_schedule_id=schedules[2].id,
                created_at=datetime.utcnow() - timedelta(days=7)
            ),
            Notification(
                user_id=users[2].id,
                title='Turno modificado',
                message=f'Tu turno del día {date.today().strftime("%d/%m/%Y")} ha sido modificado',
                type='shift_modified',
                is_read=False,
                related_schedule_id=schedules[3].id,
                created_at=datetime.utcnow() - timedelta(days=1)
            )
        ]
        db.session.add_all(notifications)
        db.session.commit()
        
        print("\n✅ ¡Datos de prueba cargados exitosamente!")
        print("\n📋 Credenciales de acceso:")
        print("   Admin:")
        print("   - Email: admin@galia.com")
        print("   - Password: admin123")
        print("\n   Empleados:")
        print("   - Email: juan.perez@galia.com")
        print("   - Email: maria.garcia@galia.com")
        print("   - Email: carlos.rodriguez@galia.com")
        print("   - Email: ana.martinez@galia.com")
        print("   - Email: pedro.lopez@galia.com")
        print("   - Password (todos): empleado123")
        print("\n📊 Datos incluidos:")
        print(f"   - {len(users)} usuarios")
        print(f"   - {len(employees)} empleados")
        print(f"   - {len(categories)} categorías de gastos")
        print(f"   - {len(supplies)} suministros")
        print(f"   - {len(supply_prices)} precios de suministros")
        print(f"   - {len(expenses)} gastos")
        print(f"   - {len(schedules)} horarios")
        print(f"   - {len(shifts)} turnos")
        print(f"   - {len(sales)} ventas con {len(sale_items)} items")
        print(f"   - {len(payrolls)} nóminas")
        print(f"   - {len(notifications)} notificaciones")

if __name__ == '__main__':
    try:
        seed_data()
    except Exception as e:
        print(f"\n❌ Error al cargar datos de prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
