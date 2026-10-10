import os
import threading

import pytest

from app import create_app
from app.config import Config, config
from app.extensions import db
from app.models import User
from app.services.pos import payment_service, sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user

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


def test_two_waiters_opening_the_same_table(pg_app):
    with pg_app.app_context():
        user_id = make_user('mozo@test.com', modules=('Camarero',)).id
        table_id = make_floor()[1].id

    def open_table():
        user = db.session.get(User, user_id)
        return sale_service.open_sale(user, 'salon', table_id=table_id, people=2).id

    results = _parallel(pg_app, open_table)
    errors = [r[1] for r in results if r[0] == 'error']
    assert [r[0] for r in results].count('ok') == 1
    assert len(errors) == 1 and isinstance(errors[0], PosError) and errors[0].status == 409


def test_concurrent_payments_do_not_exceed_balance(pg_app):
    with pg_app.app_context():
        user = make_user('caja@test.com', modules=('POS',))
        cat = make_catalog()
        table = make_floor()[1]
        sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=1)
        sale_service.add_item(user, sale.id, cat.unidad.id, quantity=2)  # 1800
        sale_service.confirm_batch(user, sale.id)
        sale_service.request_bill(user, sale.id)
        ids = (user.id, sale.id, cat.debito.id)

    def pay():
        user = db.session.get(User, ids[0])
        return payment_service.add_payment(user, ids[1], ids[2], 1500).paid_total

    results = _parallel(pg_app, pay)
    assert [r[0] for r in results].count('ok') == 1
    error = next(r[1] for r in results if r[0] == 'error')
    assert isinstance(error, PosError) and error.status == 400
