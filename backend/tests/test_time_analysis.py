import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import time, date, datetime
import sqlalchemy
from app.routes.reports import distribute_shift_hours, get_sales_by_weekday, get_sales_by_hour, get_labor_by_weekday, get_labor_by_hour
from app import create_app
from app.extensions import db
from app.models.sale import Sale
from app.models.shift import Shift


def _is_sqlite(app_ctx):
    return 'sqlite' in str(app_ctx.config.get('SQLALCHEMY_DATABASE_URI', ''))


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
    if 'sqlite' in str(app_ctx.config.get('SQLALCHEMY_DATABASE_URI', '')):
        pytest.skip('extract(dow) not reliable in SQLite — PostgreSQL only')
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
    if 'sqlite' in str(app_ctx.config.get('SQLALCHEMY_DATABASE_URI', '')):
        pytest.skip('extract(hour) not reliable in SQLite — PostgreSQL only')
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


# ---- Labor by weekday and hour tests (need DB) ----

def _make_employee(db_session, suffix='A'):
    """Create a minimal Employee for testing."""
    from app.models.employee import Employee
    from app.models.user import User
    user = User(
        email=f'testworker{suffix}@example.com',
        password_hash='x',
        role='employee'
    )
    db_session.add(user)
    db_session.flush()
    emp = Employee(
        user_id=user.id,
        first_name=f'Test{suffix}',
        last_name='Worker',
        dni=f'1234567{suffix}' if suffix.isdigit() else f'0000000{ord(suffix) % 10}',
        hire_date=date(2025, 1, 1)
    )
    db_session.add(emp)
    db_session.flush()
    return emp


def test_labor_by_weekday_distributes_cost(app_ctx):
    """8h shift on Monday with tasa 1000/h → sum_costo=8000 for Monday"""
    emp = _make_employee(db.session, suffix='1')
    # 2026-07-06 is a Monday
    shift = Shift(
        employee_id=emp.id,
        schedule_id=1,
        shift_date=date(2026, 7, 6),
        start_time=time(9, 0),
        end_time=time(17, 0),
        hours=8.0
    )
    db.session.add(shift)
    db.session.commit()

    result = get_labor_by_weekday(date(2026, 7, 6), date(2026, 7, 6), tasa_horaria=1000)
    lunes = next(r for r in result if r['dow'] == 0)  # 0=Monday
    assert lunes['sum_horas'] == pytest.approx(8.0)
    assert lunes['sum_costo'] == pytest.approx(8000.0)
    assert lunes['promedio_horas'] == pytest.approx(8.0)
    assert lunes['promedio_costo'] == pytest.approx(8000.0)
    assert lunes['dias_en_rango'] == 1


def test_labor_by_weekday_returns_7_days(app_ctx):
    result = get_labor_by_weekday(date(2026, 7, 6), date(2026, 7, 6), tasa_horaria=1000)
    assert len(result) == 7


def test_labor_by_hour_distributes_fractional(app_ctx):
    """Shift 16:00-17:45 with tasa 1000/h → slot 16h=1000, slot 17h=750"""
    emp = _make_employee(db.session, suffix='2')
    shift = Shift(
        employee_id=emp.id,
        schedule_id=1,
        shift_date=date(2026, 7, 7),
        start_time=time(16, 0),
        end_time=time(17, 45),
        hours=1.75
    )
    db.session.add(shift)
    db.session.commit()

    result = get_labor_by_hour(date(2026, 7, 7), date(2026, 7, 7), tasa_horaria=1000)
    slot_16 = next((r for r in result if r['hora'] == 16), None)
    slot_17 = next((r for r in result if r['hora'] == 17), None)
    assert slot_16 is not None
    assert slot_16['sum_costo'] == pytest.approx(1000.0)
    assert slot_17 is not None
    assert slot_17['sum_costo'] == pytest.approx(750.0)
