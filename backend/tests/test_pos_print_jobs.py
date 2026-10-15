import pytest

from app.extensions import db
from app.models.pos import PrintJob, Printer
from app.services.pos import payment_service, sale_service
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401
from print_helpers import make_kitchen_product, make_printer, make_station


@pytest.fixture
def ctx(pos_app):
    user = make_user('caja@test.com', modules=('POS', 'Anular', 'Camarero'))
    cat = make_catalog()
    kitchen = make_kitchen_product()
    _salon, t1, _t2 = make_floor()
    cocina, barra = make_station('Cocina'), make_station('Barra')
    kitchen.category.station_id = cocina.id
    cat.category.station_id = barra.id
    db.session.commit()
    make_printer('Térmica cocina', station=cocina)
    make_printer('Térmica barra', station=barra)
    return user, cat, kitchen, t1, cocina, barra


def _jobs(kind='order'):
    return PrintJob.query.filter_by(kind=kind).order_by(PrintJob.id).all()


def test_batch_is_split_by_station_with_details(ctx):
    user, cat, kitchen, t1, cocina, barra = ctx
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=2)
    sale_service.add_item(user, sale.id, kitchen.variant.id, quantity=2, note='sin sal')
    sale_service.add_item(user, sale.id, cat.taza.id, modifier_option_ids=[cat.entera.id])
    sale_service.confirm_batch(user, sale.id)
    jobs = _jobs()
    assert [(j.station_id, j.batch, j.sale_id) for j in jobs] == [(cocina.id, 1, sale.id), (barra.id, 1, sale.id)]
    kitchen_doc, bar_doc = jobs[0].document, jobs[1].document
    assert kitchen_doc['title'] == 'COCINA'
    assert kitchen_doc['header'][0] == 'Mesa 1' and 'Tanda 1' in kitchen_doc['header']
    assert kitchen_doc['lines'] == [{'qty': '2', 'text': 'Tostado', 'amount': None, 'details': ['Nota: sin sal'],
                                     'strike': False}]
    assert bar_doc['title'] == 'BARRA'
    assert bar_doc['lines'][0]['text'] == 'Cortado' and bar_doc['lines'][0]['details'] == ['Entera']
    assert all(j.status == 'pending' and j.printer.station_id == j.station_id for j in jobs)


def test_category_without_station_prints_nothing(ctx):
    user, cat, _kitchen, t1, _cocina, _barra = ctx
    cat.category.station_id = None
    db.session.commit()
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale_service.confirm_batch(user, sale.id)
    assert _jobs() == []


def test_station_without_printer_is_skipped(ctx):
    user, cat, kitchen, t1, cocina, _barra = ctx
    for printer in Printer.query.filter_by(station_id=cocina.id):
        printer.is_active = False
    db.session.commit()
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    sale_service.add_item(user, sale.id, kitchen.variant.id)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale = sale_service.confirm_batch(user, sale.id)
    assert [j.document['title'] for j in _jobs()] == ['BARRA']
    assert all(i.status == 'confirmed' for i in sale.items)


def test_second_batch_gets_its_number(ctx):
    user, cat, _kitchen, t1, _cocina, _barra = ctx
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale_service.confirm_batch(user, sale.id)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale_service.confirm_batch(user, sale.id)
    assert [j.batch for j in _jobs()] == [1, 2]
    assert 'Tanda 2' in _jobs()[1].document['header']


def test_waiter_confirm_route_and_counter_payment_print(ctx, pos_app):
    user, cat, _kitchen, t1, _cocina, _barra = ctx
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('mozo@test.com', modules=('Camarero',)))
    sale = client.post('/api/v1/pos/sales', json={'sale_type': 'salon', 'table_id': t1.id, 'people': 1},
                       headers=headers).get_json()
    client.post(f"/api/v1/pos/sales/{sale['id']}/items", json={'product_variant_id': cat.unidad.id}, headers=headers)
    assert client.post(f"/api/v1/pos/sales/{sale['id']}/confirm", headers=headers).status_code == 200
    counter = sale_service.open_sale(user, 'counter')
    sale_service.add_item(user, counter.id, cat.unidad.id)
    payment_service.add_payment(user, counter.id, cat.efectivo.id, 900)
    jobs = _jobs()
    assert len(jobs) == 2 and jobs[1].document['header'][0] == f'Mostrador #{counter.number}'


def test_cancelling_items_and_sales_prints_voids(ctx):
    user, cat, kitchen, t1, cocina, barra = ctx
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    sale_service.add_item(user, sale.id, kitchen.variant.id)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale = sale_service.confirm_batch(user, sale.id)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    pending = sale.items[-1]
    sale_service.delete_item(user, sale.id, pending.id)
    assert _jobs('void') == []
    bar_item = next(i for i in sale.items if i.product_name == 'Medialuna')
    sale_service.cancel_item(user, sale.id, bar_item.id, 'Error de carga')
    voids = _jobs('void')
    assert [(v.station_id, v.document['title']) for v in voids] == [(barra.id, 'ANULACIÓN · BARRA')]
    assert voids[0].document['lines'][0]['strike'] is True
    assert 'Motivo: Error de carga' in voids[0].document['footer']
    sale_service.cancel_sale(user, sale.id, 'Se fueron')
    assert sorted(v.station_id for v in _jobs('void')[1:]) == sorted([cocina.id, barra.id])
