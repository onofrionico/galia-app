import os
import threading

import pytest

from app import create_app
from app.config import Config, config
from app.extensions import db
from app.models import User
from app.services.pos import cash_service
from app.services.pos.errors import PosError
from cash_helpers import make_methods, make_register
from pos_helpers import make_user

PG_URL = os.getenv('POS_PG_TEST_URL')
pytestmark = pytest.mark.skipif(not PG_URL, reason='POS_PG_TEST_URL no configurada')
if PG_URL and 'test' not in PG_URL.rsplit('/', 1)[-1]:
    pytestmark = pytest.mark.skip(
        reason='POS_PG_TEST_URL tiene que apuntar a una base de test (el nombre debe contener "test")')


class PgTestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = PG_URL


@pytest.fixture
def pg_app():
    config['pos_pg_test'] = PgTestConfig
    app = create_app('pos_pg_test')
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def _parallel(app, fn, workers=2):
    barrier = threading.Barrier(workers)
    results = [None] * workers

    def run(index):
        with app.app_context():
            barrier.wait()
            try:
                results[index] = ('ok', fn())
            except Exception as exc:  # noqa: BLE001 - el test inspecciona el error
                db.session.rollback()
                results[index] = ('error', exc)
            finally:
                db.session.remove()

    threads = [threading.Thread(target=run, args=(i,)) for i in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def _single_winner(results):
    errors = [r[1] for r in results if r[0] == 'error']
    assert [r[0] for r in results].count('ok') == 1
    assert len(errors) == 1 and isinstance(errors[0], PosError) and errors[0].status == 409


def test_two_cashiers_opening_the_same_register(pg_app):
    with pg_app.app_context():
        user_id = make_user('caja@test.com', modules=('POS',)).id
        register_id = make_register().id

    def open_register():
        return cash_service.open_session(db.session.get(User, user_id), register_id, 0).id

    _single_winner(_parallel(pg_app, open_register))


def test_two_cashiers_closing_the_same_session(pg_app):
    with pg_app.app_context():
        user = make_user('caja@test.com', modules=('POS',))
        user_id = user.id
        cash_id = make_methods().efectivo.id
        session_id = cash_service.open_session(user, make_register().id, 0).id

    def close():
        user = db.session.get(User, user_id)
        return cash_service.close_session(user, session_id, [{'payment_method_id': cash_id, 'counted': 0}], None).id

    _single_winner(_parallel(pg_app, close))
