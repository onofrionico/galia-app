"""
Utilidades para manejo de zona horaria Argentina (UTC-3)
"""
from datetime import datetime, timedelta
import pytz

# Zona horaria de Argentina
ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

# Hora local en la que empieza el día comercial (las ventas de la madrugada son del día anterior)
BUSINESS_DAY_CUTOFF_HOUR = 6


def get_current_time_argentina():
    """
    Obtiene la hora actual en la zona horaria de Argentina (UTC-3)
    
    Returns:
        datetime: Datetime con timezone de Argentina
    """
    return datetime.now(ARGENTINA_TZ)


def get_current_date_argentina():
    """
    Obtiene la fecha actual en la zona horaria de Argentina
    
    Returns:
        date: Fecha actual en Argentina
    """
    return get_current_time_argentina().date()


def business_date(utc_datetime):
    """
    Día comercial de un instante UTC: la fecha en Argentina, pero lo ocurrido
    antes de BUSINESS_DAY_CUTOFF_HOUR cuenta para el día anterior
    (una mesa cerrada a la 1 de la madrugada es del turno noche previo).

    Args:
        utc_datetime: datetime en UTC (naive o con timezone)

    Returns:
        date: día comercial
    """
    local = convert_utc_to_argentina(utc_datetime)
    return (local - timedelta(hours=BUSINESS_DAY_CUTOFF_HOUR)).date()


def get_current_time_only_argentina():
    """
    Obtiene solo la hora actual en la zona horaria de Argentina
    
    Returns:
        time: Hora actual en Argentina (sin fecha)
    """
    return get_current_time_argentina().time()


def convert_utc_to_argentina(utc_datetime):
    """
    Convierte un datetime UTC a zona horaria Argentina
    
    Args:
        utc_datetime: datetime en UTC
        
    Returns:
        datetime: datetime en zona horaria Argentina
    """
    if utc_datetime.tzinfo is None:
        # Si no tiene timezone, asumimos que es UTC
        utc_datetime = pytz.utc.localize(utc_datetime)
    
    return utc_datetime.astimezone(ARGENTINA_TZ)


def convert_argentina_to_utc(argentina_datetime):
    """
    Convierte un datetime de Argentina a UTC
    
    Args:
        argentina_datetime: datetime en zona horaria Argentina
        
    Returns:
        datetime: datetime en UTC
    """
    if argentina_datetime.tzinfo is None:
        # Si no tiene timezone, asumimos que es Argentina
        argentina_datetime = ARGENTINA_TZ.localize(argentina_datetime)
    
    return argentina_datetime.astimezone(pytz.utc)


def localize_to_argentina(naive_datetime):
    """
    Agrega timezone de Argentina a un datetime naive
    
    Args:
        naive_datetime: datetime sin timezone
        
    Returns:
        datetime: datetime con timezone Argentina
    """
    return ARGENTINA_TZ.localize(naive_datetime)


def is_same_day_argentina(datetime1, datetime2):
    """
    Verifica si dos datetimes corresponden al mismo día en Argentina
    
    Args:
        datetime1: primer datetime
        datetime2: segundo datetime
        
    Returns:
        bool: True si son el mismo día en Argentina
    """
    dt1_arg = convert_utc_to_argentina(datetime1) if datetime1.tzinfo else localize_to_argentina(datetime1)
    dt2_arg = convert_utc_to_argentina(datetime2) if datetime2.tzinfo else localize_to_argentina(datetime2)
    
    return dt1_arg.date() == dt2_arg.date()
