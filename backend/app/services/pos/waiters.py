"""Quién puede figurar como mozo de una venta: usuarios activos con POS o Camarero (o admin)."""
from app.extensions import db
from app.models import User
from app.services.pos.common import display_name, parse_id
from app.services.pos.errors import bad_request
from app.utils.permissions import check_module_access

WAITER_MODULES = ('POS', 'Camarero')


def is_waiter(user):
    return (user is not None and user.is_active
            and any(check_module_access(user, module) for module in WAITER_MODULES))


def list_waiters():
    users = [u for u in User.query.filter_by(is_active=True).all() if is_waiter(u)]
    return sorted(users, key=lambda u: (display_name(u) or '').lower())


def get_waiter(waiter_id):
    user = db.session.get(User, parse_id(waiter_id, 'El mozo'))
    if not is_waiter(user):
        raise bad_request('El mozo no existe o no tiene permiso de Camarero ni de POS')
    return user
