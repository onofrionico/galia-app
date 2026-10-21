"""Fecha comercial de las ventas y sueldos prorrateados en los reportes."""
from datetime import date, datetime, timezone

import pytest

from app import create_app
from app.extensions import db
from app.models.payroll import Payroll
from app.routes.fudo_sync import parse_fudo_sale
from app.routes.reports import get_payroll_metrics
from app.utils.timezone_utils import business_date


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# ---- business_date ----

def test_business_date_evening_in_argentina_is_same_local_day():
    # 01:30 UTC del 1/10 = 22:30 del 30/9 en Argentina
    assert business_date(datetime(2026, 10, 1, 1, 30)) == date(2026, 9, 30)


def test_business_date_after_midnight_belongs_to_previous_day():
    # 07:30 UTC = 04:30 en Argentina, antes del corte de las 6
    assert business_date(datetime(2026, 10, 1, 7, 30)) == date(2026, 9, 30)


def test_business_date_after_cutoff_is_new_day():
    # 09:30 UTC = 06:30 en Argentina
    assert business_date(datetime(2026, 10, 1, 9, 30)) == date(2026, 10, 1)


def test_business_date_accepts_aware_datetimes():
    assert business_date(datetime(2026, 10, 1, 1, 30, tzinfo=timezone.utc)) == date(2026, 9, 30)


# ---- Fudo y POS usan la fecha comercial ----

def test_fudo_sale_closed_at_night_keeps_local_day():
    parsed = parse_fudo_sale({'id': '1', 'attributes': {
        'createdAt': '2026-09-30T23:00:00Z', 'closedAt': '2026-10-01T01:30:00Z',
        'status': 'CLOSED', 'total': 1000,
    }})
    assert parsed['fecha'] == date(2026, 9, 30)


def test_fudo_sale_without_close_uses_creation_business_day():
    parsed = parse_fudo_sale({'id': '2', 'attributes': {
        'createdAt': '2026-10-01T02:00:00Z', 'status': 'OPEN', 'total': 0,
    }})
    assert parsed['fecha'] == date(2026, 9, 30)


# ---- Sueldos prorrateados por días del período ----

def _payroll(year, month, gross, hours, extra=0):
    db.session.add(Payroll(employee_id=1, generated_by=1, year=year, month=month, hours_worked=hours,
                           hourly_rate=1, gross_salary=gross, extraordinary_amount=extra))
    db.session.commit()


def test_full_month_counts_whole_payroll(app):
    _payroll(2026, 9, 300000, 150, extra=30000)
    data = get_payroll_metrics(date(2026, 9, 1), date(2026, 9, 30))
    assert data['total'] == pytest.approx(330000)
    assert data['horas'] == pytest.approx(150)


def test_single_day_counts_its_share_of_the_month(app):
    _payroll(2026, 9, 300000, 150)
    data = get_payroll_metrics(date(2026, 9, 10), date(2026, 9, 10))
    assert data['total'] == pytest.approx(10000)
    assert data['horas'] == pytest.approx(5)


def test_week_across_months_prorates_each_month(app):
    _payroll(2026, 9, 300000, 150)   # 30 días → 10000/día
    _payroll(2026, 10, 310000, 155)  # 31 días → 10000/día
    data = get_payroll_metrics(date(2026, 9, 28), date(2026, 10, 4))
    assert data['total'] == pytest.approx(70000)
    assert data['horas'] == pytest.approx(35)


def test_sac_is_accrued_over_its_semester(app):
    _payroll(2026, 13, 181000, 0)  # SAC1: enero–junio 2026 = 181 días
    _payroll(2026, 14, 184000, 0)  # SAC2: julio–diciembre 2026 = 184 días
    assert get_payroll_metrics(date(2026, 3, 1), date(2026, 3, 31))['total'] == pytest.approx(31000)
    assert get_payroll_metrics(date(2026, 1, 1), date(2026, 12, 31))['total'] == pytest.approx(365000)
