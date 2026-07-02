import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import time, date, datetime
from app.routes.reports import distribute_shift_hours, get_sales_by_weekday, get_sales_by_hour
from app import create_app
from app.extensions import db
from app.models.sale import Sale


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield app


# ---- distribute_shift_hours tests (no DB) ----

def test_distribute_full_hour():
    result = distribute_shift_hours(time(10, 0), time(11, 0))
    assert result == {10: pytest.approx(1.0)}

def test_distribute_fractional_end():
    result = distribute_shift_hours(time(16, 0), time(17, 45))
    assert result[16] == pytest.approx(1.0)
    assert result[17] == pytest.approx(0.75)

def test_distribute_fractional_start():
    result = distribute_shift_hours(time(16, 30), time(18, 0))
    assert result[16] == pytest.approx(0.5)
    assert result[17] == pytest.approx(1.0)

def test_distribute_fractional_both():
    result = distribute_shift_hours(time(16, 30), time(17, 45))
    assert result[16] == pytest.approx(0.5)
    assert result[17] == pytest.approx(0.75)

def test_distribute_multi_hour():
    result = distribute_shift_hours(time(9, 0), time(12, 0))
    assert result == {9: pytest.approx(1.0), 10: pytest.approx(1.0), 11: pytest.approx(1.0)}

def test_distribute_total_hours_preserved():
    result = distribute_shift_hours(time(8, 30), time(16, 45))
    assert sum(result.values()) == pytest.approx(8.25)

def test_distribute_midnight_crossing():
    result = distribute_shift_hours(time(23, 0), time(1, 0))
    assert result[23] == pytest.approx(1.0)
    assert result[0] == pytest.approx(1.0)


# ---- Sales by weekday and hour tests (need DB) ----

def test_sales_by_weekday_sums_correctly(app_ctx):
    """Two sales on a Monday → correct sum, promedio = sum / 1 Monday in range"""
    # 2026-07-06 is a Monday
    sale1 = Sale(
        fecha=date(2026, 7, 6),
        creacion=datetime(2026, 7, 6, 12, 0, 0),
        cerrada=datetime(2026, 7, 6, 13, 0, 0),
        total=10000,
        estado='Cerrada'
    )
    sale2 = Sale(
        fecha=date(2026, 7, 6),
        creacion=datetime(2026, 7, 6, 20, 0, 0),
        cerrada=datetime(2026, 7, 6, 21, 0, 0),
        total=5000,
        estado='Cerrada'
    )
    db.session.add_all([sale1, sale2])
    db.session.commit()

    result = get_sales_by_weekday(date(2026, 7, 6), date(2026, 7, 6))
    lunes = next(r for r in result if r['dow'] == 0)  # 0=Monday
    assert lunes['sum_ventas'] == pytest.approx(15000)
    assert lunes['count_ventas'] == 2
    assert lunes['promedio_ventas'] == pytest.approx(15000)  # 1 Monday in range
    assert lunes['dias_en_rango'] == 1


def test_sales_by_weekday_returns_all_7_days(app_ctx):
    """Always returns 7 days even with no sales"""
    result = get_sales_by_weekday(date(2026, 7, 6), date(2026, 7, 6))
    assert len(result) == 7


def test_sales_by_weekday_excludes_non_closed(app_ctx):
    """Sales with estado != 'Cerrada' are excluded"""
    sale = Sale(
        fecha=date(2026, 7, 6),
        creacion=datetime(2026, 7, 6, 12, 0, 0),
        cerrada=datetime(2026, 7, 6, 13, 0, 0),
        total=9999,
        estado='Abierta'
    )
    db.session.add(sale)
    db.session.commit()

    result = get_sales_by_weekday(date(2026, 7, 6), date(2026, 7, 6))
    lunes = next(r for r in result if r['dow'] == 0)
    assert lunes['sum_ventas'] == 0


def test_sales_by_hour_groups_correctly(app_ctx):
    """Two sales in hour 12 → correct sum and promedio"""
    sale1 = Sale(
        fecha=date(2026, 7, 7),
        creacion=datetime(2026, 7, 7, 12, 0, 0),
        cerrada=datetime(2026, 7, 7, 12, 30, 0),
        total=3000,
        estado='Cerrada'
    )
    sale2 = Sale(
        fecha=date(2026, 7, 7),
        creacion=datetime(2026, 7, 7, 12, 45, 0),
        cerrada=datetime(2026, 7, 7, 12, 50, 0),
        total=2000,
        estado='Cerrada'
    )
    db.session.add_all([sale1, sale2])
    db.session.commit()

    result = get_sales_by_hour(date(2026, 7, 7), date(2026, 7, 7))
    hora_12 = next((r for r in result if r['hora'] == 12), None)
    assert hora_12 is not None
    assert hora_12['sum_ventas'] == pytest.approx(5000)
    assert hora_12['count_ventas'] == 2
    assert hora_12['promedio_ventas'] == pytest.approx(2500)
