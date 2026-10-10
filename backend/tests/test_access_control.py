import pytest
from flask import jsonify

from app import create_app
from app.extensions import db
from app.models import Module, RolePermission, UserPermission, User
from app.utils.decorators import admin_required, authenticated_only, module_required
from app.utils.jwt_utils import token_required
from app.utils.permissions import (
    check_module_access,
    get_user_modules,
    sync_role_permissions,
    sync_user_permissions,
)


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _user(email, role):
    user = User(email=email, role=role, is_active=True)
    user.set_password('secret123')
    db.session.add(user)
    db.session.commit()
    return user


def _module(name, active=True):
    module = Module(name=name, display_name=name, is_active=active)
    db.session.add(module)
    db.session.commit()
    return module


def test_admin_always_has_access_even_without_catalog(app):
    admin = _user('a@test.com', 'admin')
    assert check_module_access(admin, 'Products') is True


def test_employee_denied_when_module_missing(app):
    employee = _user('e@test.com', 'employee')
    assert check_module_access(employee, 'Products') is False


def test_employee_allowed_by_role_permission(app):
    employee = _user('e@test.com', 'employee')
    module = _module('Products')
    db.session.add(RolePermission(role='employee', module_id=module.id, is_granted=True))
    db.session.commit()
    assert check_module_access(employee, 'Products') is True


def test_user_override_beats_role_permission(app):
    employee = _user('e@test.com', 'employee')
    module = _module('Products')
    db.session.add(RolePermission(role='employee', module_id=module.id, is_granted=True))
    db.session.add(UserPermission(user_id=employee.id, module_id=module.id, is_granted=False))
    db.session.commit()
    assert check_module_access(employee, 'Products') is False


def test_inactive_module_denies(app):
    employee = _user('e@test.com', 'employee')
    module = _module('Products', active=False)
    db.session.add(RolePermission(role='employee', module_id=module.id, is_granted=True))
    db.session.commit()
    assert check_module_access(employee, 'Products') is False


def test_get_user_modules_for_employee_lists_only_granted(app):
    employee = _user('e@test.com', 'employee')
    granted = _module('MySchedule')
    _module('Payroll')
    db.session.add(RolePermission(role='employee', module_id=granted.id, is_granted=True))
    db.session.commit()
    assert [m.name for m in get_user_modules(employee)] == ['MySchedule']


def test_module_required_returns_403_for_employee(app):
    employee = _user('e@test.com', 'employee')

    @module_required('Products')
    def view(current_user):
        return jsonify({'ok': True})

    with app.test_request_context('/x'):
        response, status = view(employee)
    assert status == 403


def test_module_required_lets_admin_through(app):
    admin = _user('a@test.com', 'admin')

    @module_required('Products')
    def view(current_user):
        return 'ok'

    with app.test_request_context('/x'):
        assert view(admin) == 'ok'


def test_decorators_mark_access_control():
    @admin_required
    def admin_view(current_user):
        return 'ok'

    @module_required('Products')
    def module_view(current_user):
        return 'ok'

    @authenticated_only
    def any_view(current_user):
        return 'ok'

    assert admin_view._access_control == 'admin'
    assert module_view._access_control == 'module:Products'
    assert any_view._access_control == 'authenticated'

def test_get_user_modules_includes_user_override_grant_denied_by_role(app):
    employee = _user('e@test.com', 'employee')
    module = _module('Products')
    db.session.add(RolePermission(role='employee', module_id=module.id, is_granted=False))
    db.session.add(UserPermission(user_id=employee.id, module_id=module.id, is_granted=True))
    db.session.commit()
    assert [m.name for m in get_user_modules(employee)] == ['Products']


def test_sync_role_permissions_replaces_previous_rows(app):
    first = _module('Products')
    second = _module('Payroll')
    assert sync_role_permissions('employee', {first.id: True}) is True
    assert sync_role_permissions('employee', {second.id: True}) is True
    rows = RolePermission.query.filter_by(role='employee').all()
    assert [(r.module_id, r.is_granted) for r in rows] == [(second.id, True)]


def test_sync_user_permissions_skips_none_values(app):
    employee = _user('e@test.com', 'employee')
    module = _module('Products')
    db.session.add(RolePermission(role='employee', module_id=module.id, is_granted=True))
    db.session.commit()
    assert sync_user_permissions(employee.id, {module.id: None}) is True
    assert UserPermission.query.filter_by(user_id=employee.id).count() == 0
    assert check_module_access(employee, 'Products') is True


def test_access_control_marker_survives_token_required():
    @token_required
    @module_required('Products')
    def module_view(current_user):
        return 'ok'

    @token_required
    @authenticated_only
    def any_view(current_user):
        return 'ok'

    assert module_view._access_control == 'module:Products'
    assert any_view._access_control == 'authenticated'
