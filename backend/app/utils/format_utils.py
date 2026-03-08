def format_money_ar(amount):
    """
    Formatea un monto en formato argentino.
    
    Args:
        amount: Número (int, float, Decimal) o string representando el monto
        
    Returns:
        String formateado en formato argentino (ej: "1.234,56")
        
    Examples:
        >>> format_money_ar(1234.56)
        '1.234,56'
        >>> format_money_ar(1234567.89)
        '1.234.567,89'
        >>> format_money_ar(100)
        '100,00'
    """
    if amount is None:
        return "0,00"
    
    try:
        amount_float = float(amount)
    except (ValueError, TypeError):
        return "0,00"
    
    is_negative = amount_float < 0
    amount_float = abs(amount_float)
    
    integer_part = int(amount_float)
    decimal_part = round((amount_float - integer_part) * 100)
    
    if decimal_part == 100:
        integer_part += 1
        decimal_part = 0
    
    integer_str = str(integer_part)
    
    formatted_integer = ""
    for i, digit in enumerate(reversed(integer_str)):
        if i > 0 and i % 3 == 0:
            formatted_integer = "." + formatted_integer
        formatted_integer = digit + formatted_integer
    
    result = f"{formatted_integer},{decimal_part:02d}"
    
    if is_negative:
        result = "-" + result
    
    return result


def parse_money_ar(value):
    """
    Parsea un string en formato argentino a float.
    
    Args:
        value: String en formato argentino (ej: "1.234,56")
        
    Returns:
        Float representando el monto
        
    Examples:
        >>> parse_money_ar("1.234,56")
        1234.56
        >>> parse_money_ar("1.234.567,89")
        1234567.89
        >>> parse_money_ar("100,00")
        100.0
    """
    if not value:
        return 0.0
    
    if isinstance(value, (int, float)):
        return float(value)
    
    try:
        value_str = str(value).strip()
        
        is_negative = value_str.startswith('-')
        if is_negative:
            value_str = value_str[1:]
        
        value_str = value_str.replace('.', '')
        value_str = value_str.replace(',', '.')
        
        result = float(value_str)
        
        return -result if is_negative else result
    except (ValueError, AttributeError):
        return 0.0
