#!/usr/bin/env python
"""
Script de prueba para verificar que la zona horaria de Argentina funciona correctamente
"""
from datetime import datetime
import pytz

ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

def get_current_time_argentina():
    """Obtiene la hora actual en la zona horaria de Argentina (UTC-3)"""
    return datetime.now(ARGENTINA_TZ)

if __name__ == '__main__':
    # Hora UTC
    utc_time = datetime.utcnow()
    print(f"Hora UTC (UTC-0): {utc_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Hora de Argentina
    argentina_time = get_current_time_argentina()
    print(f"Hora Argentina (UTC-3): {argentina_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Solo la hora (como se guarda en la base de datos)
    time_only = argentina_time.time()
    print(f"Solo hora (formato guardado): {time_only.strftime('%H:%M:%S')}")
    
    # Diferencia
    diff = (argentina_time.replace(tzinfo=None) - utc_time).total_seconds() / 3600
    print(f"\nDiferencia horaria: {diff} horas")
    print(f"Zona horaria: {argentina_time.tzname()}")
