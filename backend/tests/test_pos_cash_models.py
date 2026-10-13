from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.pos import CashSession
from cash_helpers import make_register
from pos_helpers import make_user, pos_app  # noqa: F401


def _session(register, user, status='open'):
    return CashSession(register_id=register.id, status=status, opened_at=datetime.utcnow(), opened_by=user.id,
                       opening_float=Decimal('0'))


def test_only_one_open_session_per_register(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    register = make_register()
    db.session.add(_session(register, user))
    db.session.commit()
    db.session.add(_session(register, user))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_closed_sessions_do_not_block_a_new_open_one(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    register = make_register()
    other = make_register('Barra')
    db.session.add_all([_session(register, user, 'closed'), _session(register, user, 'closed'),
                        _session(register, user), _session(other, user)])
    db.session.commit()
    assert CashSession.query.filter_by(status='open').count() == 2
