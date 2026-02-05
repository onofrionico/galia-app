import re
from datetime import datetime, date, time

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_positive_number(value):
    """Validate that a number is positive"""
    try:
        num = float(value)
        return num > 0
    except (ValueError, TypeError):
        return False

def validate_date_range(start_date, end_date):
    """Validate that end_date is after start_date"""
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        return False
    return end_date >= start_date

def validate_time_range(start_time, end_time):
    """Validate time range (can span midnight)"""
    if not isinstance(start_time, time) or not isinstance(end_time, time):
        return False
    return True

def validate_payment_method(method):
    """Validate payment method"""
    valid_methods = ['efectivo', 'tarjeta_debito', 'tarjeta_credito', 'transferencia', 'qr']
    return method.lower() in valid_methods
