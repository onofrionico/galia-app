from app.extensions import db
from app.services.pos import payment_service, sale_service
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401

URL = '/api/v1/sales/in-progress'


def test_lists_open_and_billing_sales_with_total(pos_app):
    client = pos_app.test_client()
    viewer = make_user('ventas@test.com', modules=('Sales',))
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    open_sale = sale_service.open_sale(cashier, 'salon', table_id=t1.id, people=2)
    sale_service.add_item(cashier, open_sale.id, cat.unidad.id)
    billing = sale_service.open_sale(cashier, 'salon', table_id=t2.id, people=1)
    sale_service.add_item(cashier, billing.id, cat.unidad.id)
    sale_service.confirm_batch(cashier, billing.id)
    sale_service.request_bill(cashier, billing.id)
    counter = sale_service.open_sale(cashier, 'counter')

    data = client.get(URL, headers=auth_headers(client, viewer)).get_json()

    by_id = {s['id']: s for s in data['sales']}
    assert set(by_id) == {open_sale.id, billing.id, counter.id}
    assert by_id[open_sale.id]['status'] == 'open'
    assert by_id[open_sale.id]['place'] == 'Mesa 1 - Salón' and by_id[open_sale.id]['people'] == 2
    assert by_id[billing.id]['status'] == 'billing'
    assert by_id[counter.id]['place'] == 'Mostrador' and by_id[counter.id]['people'] is None
    assert by_id[open_sale.id]['waiter'] == 'caja@test.com'
    assert abs(data['total'] - sum(s['total'] for s in data['sales'])) < 0.001
    assert data['total'] > 0


def test_excludes_closed_cancelled_and_practice_sales(pos_app):
    client = pos_app.test_client()
    viewer = make_user('ventas@test.com', modules=('Sales',))
    cashier = make_user('caja@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    closed = sale_service.open_sale(cashier, 'counter')
    sale_service.add_item(cashier, closed.id, cat.unidad.id)
    payment_service.add_payment(cashier, closed.id, cat.efectivo.id, 900)
    cancelled = sale_service.open_sale(cashier, 'salon', table_id=t1.id, people=1)
    sale_service.cancel_sale(cashier, cancelled.id, 'Error')
    practice = sale_service.open_sale(cashier, 'salon', table_id=t2.id, people=1)
    practice.is_practice = True
    db.session.commit()

    data = client.get(URL, headers=auth_headers(client, viewer)).get_json()

    assert data == {'sales': [], 'total': 0.0}


def test_requires_sales_module(pos_app):
    client = pos_app.test_client()
    no_sales = make_user('caja@test.com', modules=('POS',))
    assert client.get(URL, headers=auth_headers(client, no_sales)).status_code == 403
    assert client.get(URL).status_code == 401
