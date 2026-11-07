"""Conversión de unidades para recetas (ingredientes -> unidad del insumo)."""
import unicodedata
from decimal import Decimal

# canónica -> (familia, factor a la unidad base de la familia: g, ml, unidad)
_CANONICAS = {
    'g': ('masa', Decimal('1')),
    'kg': ('masa', Decimal('1000')),
    'ml': ('volumen', Decimal('1')),
    'l': ('volumen', Decimal('1000')),
    'unidad': ('unidad', Decimal('1')),
}

_ALIAS = {
    'g': 'g', 'gr': 'g', 'grs': 'g', 'gramo': 'g', 'gramos': 'g',
    'kg': 'kg', 'kgs': 'kg', 'kilo': 'kg', 'kilos': 'kg',
    'kilogramo': 'kg', 'kilogramos': 'kg',
    'ml': 'ml', 'mls': 'ml', 'cc': 'ml', 'mililitro': 'ml', 'mililitros': 'ml',
    'l': 'l', 'lt': 'l', 'lts': 'l', 'litro': 'l', 'litros': 'l',
    'u': 'unidad', 'un': 'unidad', 'unid': 'unidad', 'unidad': 'unidad',
    'unidades': 'unidad',
}


def normalize_unit(unit):
    """Devuelve la unidad canónica ('g', 'kg', 'ml', 'l', 'unidad') o None."""
    if not unit:
        return None
    texto = unicodedata.normalize('NFD', str(unit))
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    texto = ''.join(texto.lower().split()).rstrip('.')
    return _ALIAS.get(texto)


def convert(quantity, from_unit, to_unit):
    """Convierte `quantity` entre unidades de la misma familia.

    Devuelve None si alguna unidad no se reconoce o son de familias distintas.
    """
    origen = normalize_unit(from_unit)
    destino = normalize_unit(to_unit)
    if origen is None or destino is None:
        return None
    familia_o, factor_o = _CANONICAS[origen]
    familia_d, factor_d = _CANONICAS[destino]
    if familia_o != familia_d:
        return None
    return Decimal(quantity) * factor_o / factor_d
