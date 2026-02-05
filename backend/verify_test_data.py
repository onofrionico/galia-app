#!/usr/bin/env python3
"""
Script para verificar que los datos de prueba se hayan cargado correctamente.

Uso:
    python verify_test_data.py
"""

import sys
import os

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

def verify_data():
    """Verifica que todos los datos de prueba estén presentes"""
    app = create_app()
    
    with app.app_context():
        print("🔍 Verificando datos de prueba...\n")
        
        errors = []
        warnings = []
        
        # Verificar usuarios
        users_count = User.query.count()
        print(f"✓ Usuarios: {users_count}")
        if users_count < 6:
            errors.append(f"Se esperaban 6 usuarios, se encontraron {users_count}")
        
        # Verificar admin
        admin = User.query.filter_by(email='admin@galia.com').first()
        if admin:
            print(f"  ✓ Admin encontrado: {admin.email}")
            if not admin.is_admin():
                errors.append("El usuario admin no tiene rol de administrador")
        else:
            errors.append("No se encontró el usuario administrador")
        
        # Verificar empleados
        employees_count = Employee.query.count()
        print(f"✓ Empleados: {employees_count}")
        if employees_count < 6:
            errors.append(f"Se esperaban 6 empleados, se encontraron {employees_count}")
        
        # Verificar horarios
        schedules_count = Schedule.query.count()
        print(f"✓ Horarios: {schedules_count}")
        if schedules_count < 4:
            warnings.append(f"Se esperaban 4 horarios, se encontraron {schedules_count}")
        
        # Verificar turnos
        shifts_count = Shift.query.count()
        print(f"✓ Turnos: {shifts_count}")
        if shifts_count < 100:
            warnings.append(f"Se esperaban ~140 turnos, se encontraron {shifts_count}")
        
        # Verificar ventas
        sales_count = Sale.query.count()
        print(f"✓ Ventas: {sales_count}")
        if sales_count < 150:
            warnings.append(f"Se esperaban ~200 ventas, se encontraron {sales_count}")
        
        # Verificar items de ventas
        sale_items_count = SaleItem.query.count()
        print(f"✓ Items de ventas: {sale_items_count}")
        
        # Verificar categorías de gastos
        expense_categories_count = ExpenseCategory.query.count()
        print(f"✓ Categorías de gastos: {expense_categories_count}")
        if expense_categories_count < 6:
            errors.append(f"Se esperaban 6 categorías de gastos, se encontraron {expense_categories_count}")
        
        # Verificar gastos
        expenses_count = Expense.query.count()
        print(f"✓ Gastos: {expenses_count}")
        if expenses_count < 20:
            warnings.append(f"Se esperaban ~30 gastos, se encontraron {expenses_count}")
        
        # Verificar suministros
        supplies_count = Supply.query.count()
        print(f"✓ Suministros: {supplies_count}")
        if supplies_count < 8:
            errors.append(f"Se esperaban 8 suministros, se encontraron {supplies_count}")
        
        # Verificar precios de suministros
        supply_prices_count = SupplyPrice.query.count()
        print(f"✓ Precios de suministros: {supply_prices_count}")
        
        # Verificar nóminas
        payrolls_count = Payroll.query.count()
        print(f"✓ Nóminas: {payrolls_count}")
        if payrolls_count < 5:
            errors.append(f"Se esperaban 5 nóminas, se encontraron {payrolls_count}")
        
        # Verificar notificaciones
        notifications_count = Notification.query.count()
        print(f"✓ Notificaciones: {notifications_count}")
        
        # Verificar logs de cambios
        change_logs_count = ScheduleChangeLog.query.count()
        print(f"✓ Logs de cambios: {change_logs_count}")
        
        # Resumen
        print("\n" + "="*50)
        if errors:
            print("❌ ERRORES ENCONTRADOS:")
            for error in errors:
                print(f"   - {error}")
        
        if warnings:
            print("\n⚠️  ADVERTENCIAS:")
            for warning in warnings:
                print(f"   - {warning}")
        
        if not errors and not warnings:
            print("✅ ¡Todos los datos de prueba están correctos!")
            print("\n📋 Resumen:")
            print(f"   - {users_count} usuarios")
            print(f"   - {employees_count} empleados")
            print(f"   - {schedules_count} horarios")
            print(f"   - {shifts_count} turnos")
            print(f"   - {sales_count} ventas con {sale_items_count} items")
            print(f"   - {expenses_count} gastos en {expense_categories_count} categorías")
            print(f"   - {supplies_count} suministros con {supply_prices_count} precios")
            print(f"   - {payrolls_count} nóminas")
            print(f"   - {notifications_count} notificaciones")
            print(f"   - {change_logs_count} logs de cambios")
            
            print("\n🎯 Credenciales de acceso:")
            print("   Admin: admin@galia.com / admin123")
            print("   Empleados: [nombre]@galia.com / empleado123")
            
            return 0
        elif not errors:
            print("\n✅ Datos cargados correctamente (con advertencias menores)")
            return 0
        else:
            print("\n❌ Hay errores que deben corregirse")
            return 1

if __name__ == '__main__':
    sys.exit(verify_data())
