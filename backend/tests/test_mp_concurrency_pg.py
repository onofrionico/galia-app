import os
import threading
from decimal import Decimal

import pytest

from app import create_app
from app.config import Config, config
from app.extensions import db
from app.models import PosPayment
from app.services import mercadopago
from app.services.mercadopago import point_service
from app.services.mercadopago.fake import FakeMercadoPago
from mp_helpers import billing_sale, configure_mp
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


def test_webhook_and_refresh_apply_once(pg_app, monkeypatch):
    FakeMercadoPago.reset()
    monkeypatch.setattr(mercadopago, 'get_client', lambda settings: FakeMercadoPago())
    with pg_app.app_context():
        user = make_user('caja@test.com', modules=('POS',))
        cat = make_catalog()
        _salon, t1, _t2 = make_floor()
        configure_mp()
        sale = billing_sale(user, cat, t1)
        order = point_service.start(user, sale.id, Decimal('1800'))
        FakeMercadoPago().simulate(order.mp_order_id, 'approved')
        order_id = order.id
    barrier = threading.Barrier(2)

    def run():
        with pg_app.app_context():
            barrier.wait()
            point_service.apply(order_id)
            db.session.remove()

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    with pg_app.app_context():
        assert PosPayment.query.filter_by(client_request_id=f'mp-order-{order_id}').count() == 1
