import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.routes.reports import calculate_gao


def test_gao_normal_case():
    """GAO = margen_contribucion_total / resultado_operativo"""
    result = calculate_gao(
        ventas=100000,
        costos_variables=40000,
        resultado_operativo=30000
    )
    assert result['estado'] == 'ok'
    assert result['gao'] == pytest.approx(2.0, rel=1e-3)
    assert result['margen_contribucion_total'] == 60000
    assert result['resultado_operativo'] == 30000
    assert result['interpretacion'] == 'medio'
    assert result['recomendacion'] == 'equilibrado'


def test_gao_alto():
    result = calculate_gao(
        ventas=100000,
        costos_variables=20000,
        resultado_operativo=25000
    )
    assert result['estado'] == 'ok'
    assert result['gao'] == pytest.approx(3.2, rel=1e-3)
    assert result['interpretacion'] == 'alto'
    assert result['recomendacion'] == 'volumen'


def test_gao_bajo():
    result = calculate_gao(
        ventas=100000,
        costos_variables=10000,
        resultado_operativo=70000
    )
    assert result['estado'] == 'ok'
    assert result['gao'] == pytest.approx(1.29, rel=1e-2)
    assert result['interpretacion'] == 'bajo'
    assert result['recomendacion'] == 'precio'


def test_gao_en_perdida():
    result = calculate_gao(
        ventas=100000,
        costos_variables=60000,
        resultado_operativo=-10000
    )
    assert result['estado'] == 'en_perdida'
    assert result['gao'] is None
    assert result['recomendacion'] is None


def test_gao_margen_negativo():
    result = calculate_gao(
        ventas=50000,
        costos_variables=60000,
        resultado_operativo=-20000
    )
    assert result['estado'] == 'margen_negativo'
    assert result['gao'] is None


def test_gao_sin_ventas():
    result = calculate_gao(
        ventas=0,
        costos_variables=0,
        resultado_operativo=-10000
    )
    assert result['estado'] == 'sin_datos'
    assert result['gao'] is None


def test_gao_boundary_medio_at_1_5():
    """GAO == 1.5 → medio (not bajo, since threshold is < 1.5)"""
    # GAO = 90000 / 60000 = 1.5
    result = calculate_gao(
        ventas=100000,
        costos_variables=10000,
        resultado_operativo=60000
    )
    assert result['estado'] == 'ok'
    assert result['gao'] == pytest.approx(1.5, rel=1e-3)
    assert result['interpretacion'] == 'medio'


def test_gao_boundary_alto_at_3_0():
    """GAO == 3.0 → medio (not alto, since threshold is <= 3.0)"""
    # GAO = 90000 / 30000 = 3.0
    result = calculate_gao(
        ventas=100000,
        costos_variables=10000,
        resultado_operativo=30000
    )
    assert result['estado'] == 'ok'
    assert result['gao'] == pytest.approx(3.0, rel=1e-3)
    assert result['interpretacion'] == 'medio'
