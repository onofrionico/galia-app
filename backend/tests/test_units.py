"""Tests de la conversión de unidades de recetas."""
from decimal import Decimal

import pytest

from app.services.units import convert, normalize_unit


@pytest.mark.parametrize('raw,expected', [
    ('g', 'g'), ('gr', 'g'), ('Gramos', 'g'), ('KG', 'kg'), ('kilo', 'kg'),
    ('ml', 'ml'), ('cc', 'ml'), ('L', 'l'), ('lt', 'l'), ('litro', 'l'),
    ('u', 'unidad'), ('unid', 'unidad'), ('Unidades', 'unidad'),
    ('cucharada', None), ('pizca', None), ('', None), (None, None),
])
def test_normalize_unit(raw, expected):
    assert normalize_unit(raw) == expected


def test_convert_mass():
    assert convert(Decimal('250'), 'g', 'kg') == Decimal('0.25')


def test_convert_volume():
    assert convert(Decimal('1.5'), 'l', 'cc') == Decimal('1500')


def test_convert_same_unit():
    assert convert(Decimal('3'), 'unid', 'unidad') == Decimal('3')


def test_convert_cross_family_is_none():
    assert convert(Decimal('1'), 'g', 'ml') is None


def test_convert_unknown_is_none():
    assert convert(Decimal('2'), 'cucharada', 'g') is None
