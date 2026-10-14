import os
import threading

import pytest

from app import create_app
from app.config import Config, config
from app.extensions import db
from app.services.pos import print_service
from pos_helpers import make_user
from print_helpers import make_printer

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


def test_two_print_tabs_never_get_the_same_job(pg_app):
    with pg_app.app_context():
        user = make_user('caja@test.com', modules=('POS',))
        printer = make_printer('Térmica caja', cashier=True)
        for _ in range(15):
            print_service.test_print(user, printer.id)

    barrier = threading.Barrier(2)
    results = [None, None]

    def run(index):
        with pg_app.app_context():
            barrier.wait()
            results[index] = [job.id for job in print_service.claim('Caja')]
            db.session.remove()

    threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    first, second = results
    assert not set(first) & set(second)
    assert len(first) + len(second) == 15 or len(first) == 10 or len(second) == 10
