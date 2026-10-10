import pytest
from flask import jsonify

from app import create_app
from app.extensions import db
from app.models import Module, User, UserPermission
from app.utils.decorators import module_required


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _user_with(modules):
    user = User(email='u@test.com', role='employee', is_active=True)
    user.set_password('secret123')
    db.session.add(user)
    db.session.flush()
    for name in modules:
        module = Module(name=name, display_name=name, is_active=True)
        db.session.add(module)
        db.session.flush()
        db.session.add(UserPermission(user_id=user.id, module_id=module.id, is_granted=True))
    db.session.commit()
    return user


@module_required('POS', 'Camarero')
def _view(current_user):
    return jsonify({'ok': True}), 200


def test_any_of_the_modules_grants_access(app):
    user = _user_with(['Camarero'])
    with app.test_request_context('/x'):
        _response, status = _view(user)
    assert status == 200


def test_none_of_the_modules_is_403_naming_both(app):
    user = _user_with([])
    with app.test_request_context('/x'):
        response, status = _view(user)
    assert status == 403
    assert response.get_json()['message'] == 'No tienes acceso al módulo POS o Camarero'


def test_marks_all_modules():
    assert _view._access_control == 'module:POS|Camarero'


def test_requires_at_least_one_module():
    with pytest.raises(ValueError):
        module_required()
