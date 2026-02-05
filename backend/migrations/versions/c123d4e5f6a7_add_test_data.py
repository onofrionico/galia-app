"""add_test_data

Revision ID: c123d4e5f6a7
Revises: b020c4aff4de
Create Date: 2026-02-05 12:22:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash

# revision identifiers, used by Alembic.
revision = 'c123d4e5f6a7'
down_revision = 'b020c4aff4de'
branch_labels = None
depends_on = None


def upgrade():
    # Crear conexión para insertar datos
    connection = op.get_bind()
    
    # 1. USUARIOS
    users_data = [
        {
            'email': 'admin@galia.com',
            'password_hash': generate_password_hash('admin123'),
            'role': 'admin',
            'is_active': True,
            'created_at': datetime.utcnow()
        },
        {
            'email': 'juan.perez@galia.com',
            'password_hash': generate_password_hash('empleado123'),
            'role': 'employee',
            'is_active': True,
            'created_at': datetime.utcnow()
        },
        {
            'email': 'maria.garcia@galia.com',
            'password_hash': generate_password_hash('empleado123'),
            'role': 'employee',
            'is_active': True,
            'created_at': datetime.utcnow()
        },
        {
            'email': 'carlos.rodriguez@galia.com',
            'password_hash': generate_password_hash('empleado123'),
            'role': 'employee',
            'is_active': True,
            'created_at': datetime.utcnow()
        },
        {
            'email': 'ana.martinez@galia.com',
            'password_hash': generate_password_hash('empleado123'),
            'role': 'employee',
            'is_active': True,
            'created_at': datetime.utcnow()
        },
        {
            'email': 'pedro.lopez@galia.com',
            'password_hash': generate_password_hash('empleado123'),
            'role': 'employee',
            'is_active': True,
            'created_at': datetime.utcnow()
        }
    ]
    
    for user in users_data:
        connection.execute(
            sa.text("""
                INSERT INTO users (email, password_hash, role, is_active, created_at)
                VALUES (:email, :password_hash, :role, :is_active, :created_at)
            """),
            user
        )
    
    # 2. EMPLEADOS
    employees_data = [
        {
            'user_id': 1,
            'full_name': 'Administrador Galia',
            'hourly_rate': 2500.00,
            'hire_date': date(2024, 1, 1),
            'created_at': datetime.utcnow()
        },
        {
            'user_id': 2,
            'full_name': 'Juan Pérez',
            'hourly_rate': 1800.00,
            'hire_date': date(2024, 3, 15),
            'created_at': datetime.utcnow()
        },
        {
            'user_id': 3,
            'full_name': 'María García',
            'hourly_rate': 1900.00,
            'hire_date': date(2024, 2, 1),
            'created_at': datetime.utcnow()
        },
        {
            'user_id': 4,
            'full_name': 'Carlos Rodríguez',
            'hourly_rate': 1750.00,
            'hire_date': date(2024, 4, 10),
            'created_at': datetime.utcnow()
        },
        {
            'user_id': 5,
            'full_name': 'Ana Martínez',
            'hourly_rate': 2000.00,
            'hire_date': date(2024, 1, 20),
            'created_at': datetime.utcnow()
        },
        {
            'user_id': 6,
            'full_name': 'Pedro López',
            'hourly_rate': 1850.00,
            'hire_date': date(2024, 5, 5),
            'created_at': datetime.utcnow()
        }
    ]
    
    for employee in employees_data:
        connection.execute(
            sa.text("""
                INSERT INTO employees (user_id, full_name, hourly_rate, hire_date, created_at)
                VALUES (:user_id, :full_name, :hourly_rate, :hire_date, :created_at)
            """),
            employee
        )
    
    # 3. CATEGORÍAS DE GASTOS
    expense_categories_data = [
        {'name': 'Alimentos', 'description': 'Compra de ingredientes y alimentos', 'is_active': True},
        {'name': 'Servicios', 'description': 'Luz, agua, gas, internet', 'is_active': True},
        {'name': 'Mantenimiento', 'description': 'Reparaciones y mantenimiento', 'is_active': True},
        {'name': 'Limpieza', 'description': 'Productos de limpieza', 'is_active': True},
        {'name': 'Equipamiento', 'description': 'Compra de equipos y utensilios', 'is_active': True},
        {'name': 'Marketing', 'description': 'Publicidad y promoción', 'is_active': True}
    ]
    
    for category in expense_categories_data:
        connection.execute(
            sa.text("""
                INSERT INTO expense_categories (name, description, is_active)
                VALUES (:name, :description, :is_active)
            """),
            category
        )
    
    # 4. SUMINISTROS
    supplies_data = [
        {'name': 'Café en grano', 'unit': 'kg', 'is_active': True, 'created_at': datetime.utcnow()},
        {'name': 'Leche', 'unit': 'litros', 'is_active': True, 'created_at': datetime.utcnow()},
        {'name': 'Azúcar', 'unit': 'kg', 'is_active': True, 'created_at': datetime.utcnow()},
        {'name': 'Vasos descartables', 'unit': 'unidades', 'is_active': True, 'created_at': datetime.utcnow()},
        {'name': 'Servilletas', 'unit': 'paquetes', 'is_active': True, 'created_at': datetime.utcnow()},
        {'name': 'Pan', 'unit': 'kg', 'is_active': True, 'created_at': datetime.utcnow()},
        {'name': 'Medialunas', 'unit': 'docenas', 'is_active': True, 'created_at': datetime.utcnow()},
        {'name': 'Facturas', 'unit': 'docenas', 'is_active': True, 'created_at': datetime.utcnow()}
    ]
    
    for supply in supplies_data:
        connection.execute(
            sa.text("""
                INSERT INTO supplies (name, unit, is_active, created_at)
                VALUES (:name, :unit, :is_active, :created_at)
            """),
            supply
        )
    
    # 5. PRECIOS DE SUMINISTROS (últimos 30 días)
    base_date = date.today() - timedelta(days=30)
    supply_prices_data = []
    
    # Café en grano
    for i in range(0, 31, 7):
        supply_prices_data.append({
            'supply_id': 1,
            'price': 8500.00 + (i * 50),
            'recorded_at': base_date + timedelta(days=i),
            'supplier': 'Café Premium SA',
            'notes': 'Café colombiano',
            'created_by': 1
        })
    
    # Leche
    for i in range(0, 31, 3):
        supply_prices_data.append({
            'supply_id': 2,
            'price': 450.00 + (i * 5),
            'recorded_at': base_date + timedelta(days=i),
            'supplier': 'Lácteos del Sur',
            'notes': None,
            'created_by': 1
        })
    
    # Azúcar
    for i in range(0, 31, 10):
        supply_prices_data.append({
            'supply_id': 3,
            'price': 1200.00 + (i * 10),
            'recorded_at': base_date + timedelta(days=i),
            'supplier': 'Distribuidora Central',
            'notes': None,
            'created_by': 1
        })
    
    for price in supply_prices_data:
        connection.execute(
            sa.text("""
                INSERT INTO supply_prices (supply_id, price, recorded_at, supplier, notes, created_by)
                VALUES (:supply_id, :price, :recorded_at, :supplier, :notes, :created_by)
            """),
            price
        )
    
    # 6. GASTOS (últimos 30 días)
    expenses_data = []
    for i in range(30):
        expense_date = base_date + timedelta(days=i)
        
        # Gasto de alimentos cada 3 días
        if i % 3 == 0:
            expenses_data.append({
                'amount': 15000.00 + (i * 100),
                'expense_date': expense_date,
                'category_id': 1,
                'description': f'Compra de ingredientes para cafetería - {expense_date.strftime("%d/%m/%Y")}',
                'supplier': 'Mercado Central',
                'created_by': 1,
                'created_at': datetime.combine(expense_date, time(10, 0))
            })
        
        # Servicios cada 10 días
        if i % 10 == 0:
            expenses_data.append({
                'amount': 8500.00,
                'expense_date': expense_date,
                'category_id': 2,
                'description': 'Pago de servicios',
                'supplier': 'Varios',
                'created_by': 1,
                'created_at': datetime.combine(expense_date, time(11, 0))
            })
        
        # Limpieza cada 7 días
        if i % 7 == 0:
            expenses_data.append({
                'amount': 3500.00,
                'expense_date': expense_date,
                'category_id': 4,
                'description': 'Productos de limpieza',
                'supplier': 'Limpieza Total',
                'created_by': 1,
                'created_at': datetime.combine(expense_date, time(14, 0))
            })
    
    for expense in expenses_data:
        connection.execute(
            sa.text("""
                INSERT INTO expenses (amount, expense_date, category_id, description, supplier, created_by, created_at)
                VALUES (:amount, :expense_date, :category_id, :description, :supplier, :created_by, :created_at)
            """),
            expense
        )
    
    # 7. HORARIOS (últimas 4 semanas)
    schedules_data = []
    for week in range(4):
        start_date = date.today() - timedelta(days=28) + timedelta(weeks=week)
        end_date = start_date + timedelta(days=6)
        
        schedules_data.append({
            'start_date': start_date,
            'end_date': end_date,
            'status': 'published' if week < 3 else 'draft',
            'created_by': 1,
            'created_at': datetime.combine(start_date - timedelta(days=3), time(9, 0)),
            'updated_at': datetime.combine(start_date - timedelta(days=1), time(15, 0))
        })
    
    for schedule in schedules_data:
        connection.execute(
            sa.text("""
                INSERT INTO schedules (start_date, end_date, status, created_by, created_at, updated_at)
                VALUES (:start_date, :end_date, :status, :created_by, :created_at, :updated_at)
            """),
            schedule
        )
    
    # 8. TURNOS (para cada horario)
    shifts_data = []
    for schedule_id in range(1, 5):
        schedule_start = date.today() - timedelta(days=28) + timedelta(weeks=schedule_id-1)
        
        for day in range(7):
            shift_date = schedule_start + timedelta(days=day)
            
            # Turno mañana - 2 empleados
            shifts_data.append({
                'schedule_id': schedule_id,
                'employee_id': 2,  # Juan
                'shift_date': shift_date,
                'start_time': time(7, 0),
                'end_time': time(15, 0),
                'hours': 8.0,
                'created_at': datetime.utcnow()
            })
            
            shifts_data.append({
                'schedule_id': schedule_id,
                'employee_id': 3,  # María
                'shift_date': shift_date,
                'start_time': time(8, 0),
                'end_time': time(16, 0),
                'hours': 8.0,
                'created_at': datetime.utcnow()
            })
            
            # Turno tarde - 2 empleados
            shifts_data.append({
                'schedule_id': schedule_id,
                'employee_id': 4,  # Carlos
                'shift_date': shift_date,
                'start_time': time(15, 0),
                'end_time': time(23, 0),
                'hours': 8.0,
                'created_at': datetime.utcnow()
            })
            
            shifts_data.append({
                'schedule_id': schedule_id,
                'employee_id': 5,  # Ana
                'shift_date': shift_date,
                'start_time': time(16, 0),
                'end_time': time(22, 0),
                'hours': 6.0,
                'created_at': datetime.utcnow()
            })
            
            # Fin de semana - turno extra
            if day >= 5:  # Sábado y domingo
                shifts_data.append({
                    'schedule_id': schedule_id,
                    'employee_id': 6,  # Pedro
                    'shift_date': shift_date,
                    'start_time': time(9, 0),
                    'end_time': time(17, 0),
                    'hours': 8.0,
                    'created_at': datetime.utcnow()
                })
    
    for shift in shifts_data:
        connection.execute(
            sa.text("""
                INSERT INTO shifts (schedule_id, employee_id, shift_date, start_time, end_time, hours, created_at)
                VALUES (:schedule_id, :employee_id, :shift_date, :start_time, :end_time, :hours, :created_at)
            """),
            shift
        )
    
    # 9. VENTAS (últimos 30 días)
    sales_data = []
    sale_items_data = []
    sale_id = 1
    
    for i in range(30):
        sale_date = base_date + timedelta(days=i)
        
        # 5-10 ventas por día
        num_sales = 5 + (i % 6)
        
        for sale_num in range(num_sales):
            # Distribuir ventas entre empleados
            employee_id = 2 + (sale_num % 5)
            
            # Hora de venta entre 7am y 10pm
            sale_hour = 7 + (sale_num * 2) % 15
            sale_time = datetime.combine(sale_date, time(sale_hour, (sale_num * 15) % 60))
            
            # Método de pago
            payment_methods = ['efectivo', 'tarjeta_debito', 'tarjeta_credito', 'transferencia']
            payment_method = payment_methods[sale_num % 4]
            
            # Calcular monto total (se calculará de los items)
            items_for_sale = []
            total_amount = 0
            
            # 1-4 items por venta
            num_items = 1 + (sale_num % 4)
            
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
            
            for item_num in range(num_items):
                product = products[(sale_num + item_num) % len(products)]
                quantity = 1 + (item_num % 2)
                unit_price = product['price']
                subtotal = quantity * unit_price
                total_amount += subtotal
                
                items_for_sale.append({
                    'sale_id': sale_id,
                    'description': product['desc'],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'subtotal': subtotal
                })
            
            sales_data.append({
                'id': sale_id,
                'amount': total_amount,
                'payment_method': payment_method,
                'employee_id': employee_id,
                'notes': f'Venta {sale_num + 1} del día' if sale_num % 3 == 0 else None,
                'created_at': sale_time
            })
            
            sale_items_data.extend(items_for_sale)
            sale_id += 1
    
    for sale in sales_data:
        connection.execute(
            sa.text("""
                INSERT INTO sales (id, amount, payment_method, employee_id, notes, created_at)
                VALUES (:id, :amount, :payment_method, :employee_id, :notes, :created_at)
            """),
            sale
        )
    
    for item in sale_items_data:
        connection.execute(
            sa.text("""
                INSERT INTO sale_items (sale_id, description, quantity, unit_price, subtotal)
                VALUES (:sale_id, :description, :quantity, :unit_price, :subtotal)
            """),
            item
        )
    
    # 10. NÓMINAS (último mes y mes anterior)
    current_date = date.today()
    payrolls_data = []
    
    # Mes anterior
    last_month = current_date.month - 1 if current_date.month > 1 else 12
    last_year = current_date.year if current_date.month > 1 else current_date.year - 1
    
    for employee_id in range(2, 7):
        # Calcular horas trabajadas (aproximadamente 160 horas al mes)
        hours_worked = 160.0 + (employee_id * 5)
        
        # Obtener tarifa del empleado
        hourly_rates = {2: 1800, 3: 1900, 4: 1750, 5: 2000, 6: 1850}
        hourly_rate = hourly_rates[employee_id]
        
        gross_salary = hours_worked * hourly_rate
        
        payrolls_data.append({
            'employee_id': employee_id,
            'month': last_month,
            'year': last_year,
            'hours_worked': hours_worked,
            'hourly_rate': hourly_rate,
            'gross_salary': gross_salary,
            'generated_at': datetime(last_year, last_month, 28, 10, 0),
            'generated_by': 1
        })
    
    for payroll in payrolls_data:
        connection.execute(
            sa.text("""
                INSERT INTO payrolls (employee_id, month, year, hours_worked, hourly_rate, gross_salary, generated_at, generated_by)
                VALUES (:employee_id, :month, :year, :hours_worked, :hourly_rate, :gross_salary, :generated_at, :generated_by)
            """),
            payroll
        )
    
    # 11. NOTIFICACIONES
    notifications_data = [
        {
            'user_id': 2,
            'title': 'Nuevo horario publicado',
            'message': 'Se ha publicado el horario de la semana del ' + (date.today() - timedelta(days=7)).strftime('%d/%m/%Y'),
            'type': 'schedule_change',
            'is_read': True,
            'related_schedule_id': 3,
            'related_shift_id': None,
            'created_at': datetime.utcnow() - timedelta(days=7)
        },
        {
            'user_id': 3,
            'title': 'Nuevo horario publicado',
            'message': 'Se ha publicado el horario de la semana del ' + (date.today() - timedelta(days=7)).strftime('%d/%m/%Y'),
            'type': 'schedule_change',
            'is_read': True,
            'related_schedule_id': 3,
            'related_shift_id': None,
            'created_at': datetime.utcnow() - timedelta(days=7)
        },
        {
            'user_id': 4,
            'title': 'Turno modificado',
            'message': 'Tu turno del día ' + date.today().strftime('%d/%m/%Y') + ' ha sido modificado',
            'type': 'shift_modified',
            'is_read': False,
            'related_schedule_id': 4,
            'related_shift_id': 1,
            'created_at': datetime.utcnow() - timedelta(days=1)
        },
        {
            'user_id': 5,
            'title': 'Nuevo turno asignado',
            'message': 'Se te ha asignado un nuevo turno para el ' + (date.today() + timedelta(days=2)).strftime('%d/%m/%Y'),
            'type': 'shift_added',
            'is_read': False,
            'related_schedule_id': 4,
            'related_shift_id': 2,
            'created_at': datetime.utcnow() - timedelta(hours=12)
        }
    ]
    
    for notification in notifications_data:
        connection.execute(
            sa.text("""
                INSERT INTO notifications (user_id, title, message, type, is_read, related_schedule_id, related_shift_id, created_at)
                VALUES (:user_id, :title, :message, :type, :is_read, :related_schedule_id, :related_shift_id, :created_at)
            """),
            notification
        )
    
    # 12. LOGS DE CAMBIOS EN HORARIOS
    change_logs_data = [
        {
            'schedule_id': 3,
            'shift_id': 1,
            'change_type': 'shift_added',
            'changed_by': 1,
            'affected_employee_id': 2,
            'old_data': None,
            'new_data': '{"shift_date": "' + (date.today() - timedelta(days=7)).strftime('%Y-%m-%d') + '", "start_time": "07:00", "end_time": "15:00"}',
            'created_at': datetime.utcnow() - timedelta(days=10)
        },
        {
            'schedule_id': 4,
            'shift_id': 2,
            'change_type': 'shift_modified',
            'changed_by': 1,
            'affected_employee_id': 4,
            'old_data': '{"start_time": "14:00", "end_time": "22:00"}',
            'new_data': '{"start_time": "15:00", "end_time": "23:00"}',
            'created_at': datetime.utcnow() - timedelta(days=1)
        }
    ]
    
    for log in change_logs_data:
        connection.execute(
            sa.text("""
                INSERT INTO schedule_change_logs (schedule_id, shift_id, change_type, changed_by, affected_employee_id, old_data, new_data, created_at)
                VALUES (:schedule_id, :shift_id, :change_type, :changed_by, :affected_employee_id, :old_data, :new_data, :created_at)
            """),
            log
        )
    
    print("✅ Datos de prueba insertados correctamente")
    print(f"   - {len(users_data)} usuarios")
    print(f"   - {len(employees_data)} empleados")
    print(f"   - {len(expense_categories_data)} categorías de gastos")
    print(f"   - {len(supplies_data)} suministros")
    print(f"   - {len(supply_prices_data)} precios de suministros")
    print(f"   - {len(expenses_data)} gastos")
    print(f"   - {len(schedules_data)} horarios")
    print(f"   - {len(shifts_data)} turnos")
    print(f"   - {len(sales_data)} ventas")
    print(f"   - {len(sale_items_data)} items de ventas")
    print(f"   - {len(payrolls_data)} nóminas")
    print(f"   - {len(notifications_data)} notificaciones")
    print(f"   - {len(change_logs_data)} logs de cambios")


def downgrade():
    # Eliminar datos en orden inverso para respetar las foreign keys
    connection = op.get_bind()
    
    connection.execute(sa.text("DELETE FROM schedule_change_logs"))
    connection.execute(sa.text("DELETE FROM notifications"))
    connection.execute(sa.text("DELETE FROM payrolls"))
    connection.execute(sa.text("DELETE FROM sale_items"))
    connection.execute(sa.text("DELETE FROM sales"))
    connection.execute(sa.text("DELETE FROM shifts"))
    connection.execute(sa.text("DELETE FROM schedules"))
    connection.execute(sa.text("DELETE FROM expenses"))
    connection.execute(sa.text("DELETE FROM supply_prices"))
    connection.execute(sa.text("DELETE FROM supplies"))
    connection.execute(sa.text("DELETE FROM expense_categories"))
    connection.execute(sa.text("DELETE FROM employees"))
    connection.execute(sa.text("DELETE FROM users"))
    
    print("✅ Datos de prueba eliminados correctamente")
