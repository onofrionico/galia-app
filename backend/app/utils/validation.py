from decimal import Decimal, InvalidOperation


def json_object():
    """Cuerpo JSON del request como dict, o None si falta o no es un objeto."""
    from flask import request
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def parse_decimal(value, field, minimum=Decimal('0'), maximum=None):
    """Convierte `value` a Decimal validando rango.

    `minimum` es inclusivo y `maximum` es exclusivo (coincide con la capacidad
    de la columna Numeric). Levanta ValueError con un mensaje usable en la API.
    """
    if value is None or isinstance(value, bool):
        raise ValueError(f'{field} debe ser un número')
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f'{field} debe ser un número')
    if not number.is_finite():
        raise ValueError(f'{field} debe ser un número finito')
    if minimum is not None and number < minimum:
        raise ValueError(f'{field} no puede ser menor a {minimum}')
    if maximum is not None and number >= maximum:
        raise ValueError(f'{field} es demasiado grande')
    return number


def clean_str(value, max_len=None):
    """Devuelve el string sin espacios o None si no hay texto útil."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    if max_len is not None and len(value) > max_len:
        raise ValueError(f'El texto no puede superar {max_len} caracteres')
    return value
