"""Grilla pública: los empleados ven la grilla completa solo si está publicada y marcada como pública."""
from datetime import date, time, timedelta

from app.extensions import db
from app.models.employee import Employee
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.user import User

MONDAY = date(2026, 11, 2)


def _employee(email, first_name, dni):
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, role='employee', is_active=True)
        user.set_password('secret123')
        db.session.add(user)
        db.session.flush()
    employee = Employee(user_id=user.id, first_name=first_name, last_name='Test', dni=dni, hire_date=MONDAY)
    db.session.add(employee)
    db.session.flush()
    return employee


def _schedule(admin_id, status='published', is_public=False, start=MONDAY):
    schedule = Schedule(start_date=start, end_date=start + timedelta(days=6), status=status,
                        is_public=is_public, created_by=admin_id)
    db.session.add(schedule)
    db.session.flush()
    return schedule


def _shift(schedule, employee, day_offset=0, start=time(8), end=time(14)):
    shift = Shift(schedule_id=schedule.id, employee_id=employee.id, shift_date=schedule.start_date + timedelta(days=day_offset),
                  start_time=start, end_time=end, hours=6)
    db.session.add(shift)
    db.session.flush()
    return shift


def _admin_id():
    return User.query.filter_by(role='admin').first().id


def test_team_week_only_includes_public_published_schedules(menu_client, admin_headers, employee_headers):
    me = _employee('menu-employee@test.com', 'Zoe', '11111111')
    other = _employee('otra@test.com', 'Ana', '22222222')
    public = _schedule(_admin_id(), is_public=True)
    _shift(public, me, 0)
    _shift(public, other, 1)
    private = _schedule(_admin_id(), is_public=False, start=MONDAY + timedelta(days=7))
    _shift(private, other, 0)
    draft = _schedule(_admin_id(), status='draft', is_public=True, start=MONDAY + timedelta(days=14))
    _shift(draft, other, 0)
    db.session.commit()

    week = menu_client.get('/api/v1/employee/schedule/team/weekly?start_date=2026-11-04', headers=employee_headers).get_json()
    assert week['start_date'] == '2026-11-02'
    assert len(week['days']) == 7
    # Yo primero, después el resto por nombre
    assert [e['employee_name'] for e in week['employees']] == ['Zoe Test', 'Ana Test']
    assert week['employees'][0]['is_me'] is True
    assert week['employees'][1]['shifts'][0]['shift_date'] == '2026-11-03'

    for start in ('2026-11-09', '2026-11-16'):  # privada y borrador
        week = menu_client.get(f'/api/v1/employee/schedule/team/weekly?start_date={start}', headers=employee_headers).get_json()
        assert week['employees'] == []


def test_admin_can_toggle_is_public(menu_client, admin_headers):
    schedule = _schedule(_admin_id())
    db.session.commit()

    response = menu_client.put(f'/api/v1/schedules/{schedule.id}', json={'is_public': True}, headers=admin_headers)
    assert response.status_code == 200
    assert response.get_json()['schedule']['is_public'] is True

    bad = menu_client.put(f'/api/v1/schedules/{schedule.id}', json={'is_public': 'si'}, headers=admin_headers)
    assert bad.status_code == 400


def test_employee_cannot_toggle_or_read_admin_schedules(menu_client, admin_headers, employee_headers):
    schedule = _schedule(_admin_id())
    db.session.commit()

    assert menu_client.put(f'/api/v1/schedules/{schedule.id}', json={'is_public': True}, headers=employee_headers).status_code == 403
    assert menu_client.get('/api/v1/schedules', headers=employee_headers).status_code == 403
    assert menu_client.get(f'/api/v1/schedules/{schedule.id}', headers=employee_headers).status_code == 403
