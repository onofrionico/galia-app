#!/usr/bin/env python3
"""
Script para cargar datos de prueba en la base de datos.
Este script ejecuta la migración que inserta datos de prueba completos.

Uso:
    python load_test_data.py

Nota: Asegúrate de haber ejecutado las migraciones base primero con:
    flask db upgrade
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from flask_migrate import upgrade

def main():
    """Ejecuta la migración de datos de prueba"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Ejecutando migraciones...")
            upgrade()
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
            print("   - 6 usuarios (1 admin + 5 empleados)")
            print("   - 4 horarios semanales con turnos completos")
            print("   - ~200 ventas de los últimos 30 días")
            print("   - Gastos y suministros registrados")
            print("   - Nóminas del mes anterior")
            print("   - Notificaciones de ejemplo")
            
        except Exception as e:
            print(f"\n❌ Error al cargar datos de prueba: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    main()
