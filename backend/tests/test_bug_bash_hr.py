"""Regresiones del bug bash 2026-11: RRHH, fichaje, feriados y nómina."""
from datetime import date, time, timedelta
from decimal import Decimal

import pytest

from app.extensions import db
from app.models.employee import Employee
from app.models.job_position import JobPosition
from app.models.ml_tracking import Holiday
from app.models.payroll import Payroll
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.time_tracking import TimeTracking
from app.models.user import User
from app.models.work_block import WorkBlock
from app.utils import payroll_utils


def _employee(email='emp@test.com', dni='30111222', rate='1000'):
    position = JobPosition.query.first()
    if position is None:
        position = JobPosition(name='Mozo', contract_type='por_hora', hourly_rate=Decimal(rate), is_active=True)
        db.session.add(position)
        db.session.flush()
    user = User(email=email, role='employee', is_active=True)
    user.set_password('secret123')
    db.session.add(user)
    db.session.flush()
    employee = Employee(user_id=user.id, first_name='Ana', last_name='Gomez', dni=dni,
                        hire_date=date(2024, 1, 1), status='activo', current_job_position_id=position.id)
    db.session.add(employee)
    db.session.commit()
    return employee


def _tracking(employee, day, start=time(9, 0), end=time(11, 0)):
    record = TimeTracking(employee_id=employee.id, tracking_date=day)
    db.session.add(record)
    db.session.flush()
    block = WorkBlock(time_tracking_id=record.id, start_time=start, end_time=end)
    db.session.add(block)
    db.session.commit()
    return record, block


# --- 1. Inactivar empleado --------------------------------------------------------------------

@pytest.mark.parametrize('how', ['patch', 'put'])
def test_inactivating_employee_deactivates_user_and_drops_future_shifts(menu_client, admin_headers, how):
    employee = _employee()
    admin = User.query.filter_by(email='menu-admin@test.com').first()
    schedule = Schedule(start_date=date.today(), end_date=date.today() + timedelta(days=7), created_by=admin.id)
    db.session.add(schedule)
    db.session.flush()
    db.session.add(Shift(schedule_id=schedule.id, employee_id=employee.id, shift_date=date.today() + timedelta(days=1),
                         start_time=time(9, 0), end_time=time(17, 0), hours=8))
    db.session.commit()

    if how == 'patch':
        response = menu_client.patch(f'/api/v1/employees/{employee.id}/change-status', headers=admin_headers,
                                     json={'status': 'inactivo'})
    else:
        response = menu_client.put(f'/api/v1/employees/{employee.id}', headers=admin_headers,
                                   json={'status': 'inactivo'})
    assert response.status_code == 200, response.get_data(as_text=True)
    db.session.expire_all()
    assert db.session.get(Employee, employee.id).user.is_active is False
    assert Shift.query.filter_by(employee_id=employee.id).count() == 0


# --- 2. Calendario: horas para todos, costo solo con Payroll -------------------------------------

def _calendar(client, headers, day):
    return client.get(f'/api/v1/time-tracking/calendar?year={day.year}&month={day.month}', headers=headers)


def test_calendar_hides_cost_without_payroll_access(menu_client, employee_headers):
    employee = _employee(email='other@test.com', dni='30111999')
    day = date(2026, 3, 4)
    _tracking(employee, day)
    response = _calendar(menu_client, employee_headers, day)
    assert response.status_code == 200
    body = response.get_json()
    assert 'total_cost' not in body
    assert all('daily_cost' not in d for d in body['days'])
    worked = [d for d in body['days'] if d['date'] == day.isoformat()][0]
    assert worked['employee_count'] == 1 and worked['total_hours'] == 2  # las horas siguen siendo visibles


def test_calendar_shows_cost_to_admin(menu_client, admin_headers):
    employee = _employee(rate='1000')
    day = date(2026, 3, 4)
    _tracking(employee, day)
    body = _calendar(menu_client, admin_headers, day).get_json()
    assert body['total_cost'] == pytest.approx(2000.0)
    assert [d for d in body['days'] if d['date'] == day.isoformat()][0]['daily_cost'] == pytest.approx(2000.0)


# --- 3. Fecha Argentina en el fichaje -------------------------------------------------------------

def test_check_in_uses_argentina_date(menu_client, employee_headers, monkeypatch):
    from app.routes import time_tracking
    user = User.query.filter_by(email='menu-employee@test.com').first()
    position = JobPosition(name='Mozo', contract_type='por_hora', hourly_rate=Decimal('1000'), is_active=True)
    db.session.add(position)
    db.session.flush()
    employee = Employee(user_id=user.id, first_name='Ana', last_name='Gomez', dni='30111555',
                        hire_date=date(2024, 1, 1), status='activo', current_job_position_id=position.id)
    db.session.add(employee)
    db.session.commit()
    # 00:30 UTC del 5/3 = 21:30 del 4/3 en Argentina
    monkeypatch.setattr(time_tracking, 'get_current_date_argentina', lambda: date(2026, 3, 4))
    monkeypatch.setattr(time_tracking, 'get_current_time_only_argentina', lambda: time(21, 30))
    response = menu_client.post('/api/v1/time-tracking/check-in', headers=employee_headers, json={})
    assert response.status_code in (200, 201), response.get_data(as_text=True)
    record = TimeTracking.query.filter_by(employee_id=employee.id).one()
    assert record.tracking_date == date(2026, 3, 4)


def test_schedule_service_uses_argentina_date(menu_app, monkeypatch):
    from app.services import employee_schedule_service as svc
    monkeypatch.setattr(svc, 'get_current_date_argentina', lambda: date(2026, 3, 4))
    monkeypatch.setattr(svc, 'get_current_time_only_argentina', lambda: time(21, 30))
    employee = _employee()
    admin = User(email='a@test.com', role='admin', is_active=True)
    admin.set_password('x')
    db.session.add(admin)
    db.session.flush()
    schedule = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 10), created_by=admin.id,
                        status='published')
    db.session.add(schedule)
    db.session.flush()
    db.session.add(Shift(schedule_id=schedule.id, employee_id=employee.id, shift_date=date(2026, 3, 4),
                         start_time=time(22, 0), end_time=time(23, 59), hours=2))
    db.session.commit()
    result = svc.EmployeeScheduleService.get_employee_upcoming_shifts(employee.id, days_ahead=3)
    assert result['start_date'] == '2026-03-04'  # parte del dia Argentina, no del dia UTC
    assert result['shift_count'] == 1  # el turno de las 22:00 del 4/3 todavia es "proximo" a las 21:30 AR


# --- 4. special_event no es feriado pago -----------------------------------------------------------

def test_special_event_is_not_a_paid_holiday(menu_app):
    db.session.add_all([
        Holiday(date=date(2026, 5, 25), name='Revolucion de Mayo', type='national'),
        Holiday(date=date(2026, 6, 6), name='Local', type='local'),
        Holiday(date=date(2026, 7, 11), name='Recital', type='special_event'),
        Holiday(date=date(2026, 8, 1), name='Sin tipo', type=None),
    ])
    db.session.commit()
    assert payroll_utils.is_holiday(date(2026, 5, 25)) is True
    assert payroll_utils.is_holiday(date(2026, 6, 6)) is True
    assert payroll_utils.is_holiday(date(2026, 8, 1)) is True
    assert payroll_utils.is_holiday(date(2026, 7, 11)) is False
    assert payroll_utils.is_holiday(date(2026, 7, 12)) is False


# --- 5. Bloques de horas con nomina validada --------------------------------------------------------

def _payroll(employee, month, year, status):
    admin = User.query.filter_by(role='admin').first()
    db.session.add(Payroll(employee_id=employee.id, month=month, year=year, hours_worked=Decimal('2'),
                           scheduled_hours=Decimal('2'), hourly_rate=Decimal('1000'), gross_salary=Decimal('2000'),
                           status=status, generated_by=admin.id))
    db.session.commit()


@pytest.mark.parametrize('status', ['validated', 'employee_validated'])
def test_validated_payroll_locks_work_blocks(menu_client, admin_headers, status):
    employee = _employee()
    _record, block = _tracking(employee, date(2026, 3, 4))
    _payroll(employee, 3, 2026, status)
    put = menu_client.put(f'/api/v1/payroll/work-blocks/{block.id}', headers=admin_headers,
                          json={'end_time': '12:00'})
    delete = menu_client.delete(f'/api/v1/payroll/work-blocks/{block.id}', headers=admin_headers)
    assert put.status_code == 409 and delete.status_code == 409
    db.session.expire_all()
    assert db.session.get(WorkBlock, block.id).end_time == time(11, 0)


def test_draft_payroll_allows_edit_and_delete(menu_client, admin_headers):
    employee = _employee()
    _record, block = _tracking(employee, date(2026, 3, 4))
    _payroll(employee, 3, 2026, 'draft')
    assert menu_client.put(f'/api/v1/payroll/work-blocks/{block.id}', headers=admin_headers,
                           json={'end_time': '12:00'}).status_code == 200
    assert menu_client.delete(f'/api/v1/payroll/work-blocks/{block.id}', headers=admin_headers).status_code == 200
    assert db.session.get(WorkBlock, block.id) is None


def test_work_block_rejects_start_after_end(menu_client, admin_headers):
    employee = _employee()
    _record, block = _tracking(employee, date(2026, 3, 4))
    response = menu_client.put(f'/api/v1/payroll/work-blocks/{block.id}', headers=admin_headers,
                               json={'start_time': '13:00'})
    assert response.status_code == 400
    db.session.expire_all()
    assert db.session.get(WorkBlock, block.id).start_time == time(9, 0)
