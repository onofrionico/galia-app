import os
import threading

import pytest

from app import create_app
from app.config import Config, config
from app.extensions import db
from app.models import Invoice, User
from app.services.fiscal import arca, invoice_service
from app.services.fiscal.arca.fake import FakeArca
from app.services.pos.errors import PosError
from fiscal_helpers import closed_sale, configure_fiscal
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


def test_two_cashiers_never_get_the_same_number(pg_app, monkeypatch):
    FakeArca.reset()
    monkeypatch.setattr(arca, 'get_gateway', lambda settings: FakeArca())
    with pg_app.app_context():
        user = make_user('caja@test.com', modules=('POS',))
        cat = make_catalog()
        _salon, t1, t2 = make_floor()
        configure_fiscal()
        sale_ids = [closed_sale(user, cat, t1).id, closed_sale(user, cat, t2).id]
        user_id = user.id

    barrier = threading.Barrier(2)
    results = [None, None]

    def run(index):
        with pg_app.app_context():
            barrier.wait()
            try:
                results[index] = invoice_service.issue(db.session.get(User, user_id), sale_ids[index], None).status
            except PosError as exc:
                db.session.rollback()
                results[index] = exc.message
            db.session.remove()

    threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    with pg_app.app_context():
        numbers = [i.number for i in Invoice.query.filter_by(status='authorized')]
    assert numbers and len(numbers) == len(set(numbers))
    assert all(r == 'authorized' or 'emitiéndose' in r for r in results)
