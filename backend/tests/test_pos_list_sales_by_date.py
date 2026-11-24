from datetime import date, timedelta

from app.extensions import db
from app.models.pos import PosSale
from app.services.pos import payment_service, sale_service
from pos_helpers import auth_headers, make_catalog, make_user, pos_app  # noqa: F401

URL = '/api/v1/pos/sales'


def _closed_counter_sale(cashier, cat):
    sale = sale_service.open_sale(cashier, 'counter')
    sale_service.add_item(cashier, sale.id, cat.unidad.id)
    payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 900)
    return db.session.get(PosSale, sale.id)


def test_filters_by_business_date_and_status(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS', 'Anular'))
    headers = auth_headers(client, cashier)
    cat = make_catalog()
    today_closed = _closed_counter_sale(cashier, cat)
    yesterday_closed = _closed_counter_sale(cashier, cat)
    yesterday_closed.business_date = date.today() - timedelta(days=1)
    db.session.commit()
    day = today_closed.business_date.isoformat()

    today = client.get(f'{URL}?status=closed,cancelled&date={day}', headers=headers).get_json()['sales']
    assert [s['id'] for s in today] == [today_closed.id]

    yesterday = client.get(f'{URL}?status=closed&date={yesterday_closed.business_date.isoformat()}',
                           headers=headers).get_json()['sales']
    assert [s['id'] for s in yesterday] == [yesterday_closed.id]

    no_date = client.get(f'{URL}?status=closed', headers=headers).get_json()['sales']
    assert {s['id'] for s in no_date} == {today_closed.id, yesterday_closed.id}


def test_rejects_invalid_date(pos_app):
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('caja@test.com', modules=('POS',)))
    assert client.get(f'{URL}?date=ayer', headers=headers).status_code == 400
