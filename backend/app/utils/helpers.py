from datetime import datetime, date
from decimal import Decimal

def format_currency(amount):
    """Format a number as currency (Argentine Peso)"""
    if isinstance(amount, Decimal):
        amount = float(amount)
    return f"${amount:,.2f}"

def parse_date(date_string):
    """Parse a date string in ISO format"""
    try:
        return datetime.fromisoformat(date_string).date()
    except (ValueError, AttributeError):
        return None

def parse_datetime(datetime_string):
    """Parse a datetime string in ISO format"""
    try:
        return datetime.fromisoformat(datetime_string)
    except (ValueError, AttributeError):
        return None

def get_date_range(period_type, year, month=None, week=None):
    """
    Get start and end dates for a given period
    
    Args:
        period_type: 'week', 'month', 'quarter', 'year'
        year: Year number
        month: Month number (1-12) for month/week periods
        week: Week number for week periods
    
    Returns:
        tuple: (start_date, end_date)
    """
    if period_type == 'month':
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        return start_date, end_date
    
    elif period_type == 'year':
        start_date = date(year, 1, 1)
        end_date = date(year + 1, 1, 1)
        return start_date, end_date
    
    return None, None
