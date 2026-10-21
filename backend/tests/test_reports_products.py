"""Ítems de venta (Fudo y POS) y reporte de ventas por producto."""
from datetime import date, datetime
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import ProductVariant, Sale, SaleItem
from app.services.pos import payment_service, sale_service
from app.services.sale_fudo_parsing import index_included, parse_fudo_items, parse_fudo_sale
from app.services.sales_sync_service import apply_fudo_sales
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _fudo_payload(sale_id='10', items=(('100', '7', 2, 1500, False),), closed='2026-10-01T15:00:00Z'):
    """Venta de Fudo con ítems (id, product_id, quantity, price, canceled) en formato JSON:API."""
    included = [
        {'type': 'ProductCategory', 'id': '3', 'attributes': {'name': 'Cafetería'}},
        {'type': 'Product', 'id': '7', 'attributes': {'name': 'Cortado'},
         'relationships': {'productCategory': {'data': {'type': 'ProductCategory', 'id': '3'}}}},
        {'type': 'Product', 'id': '8', 'attributes': {'name': 'Medialuna'},
         'relationships': {'productCategory': {'data': {'type': 'ProductCategory', 'id': '3'}}}},
        {'type': 'User', 'id': '4', 'attributes': {'name': 'Juan'}},
        {'type': 'Room', 'id': '5', 'attributes': {'name': 'Vereda'}},
        {'type': 'Table', 'id': '6', 'attributes': {'number': 12},
         'relationships': {'room': {'data': {'type': 'Room', 'id': '5'}}}},
        {'type': 'PaymentMethod', 'id': '9', 'attributes': {'name': 'Efectivo'}},
        {'type': 'Payment', 'id': '11', 'attributes': {'amount': 3000, 'canceled': False},
         'relationships': {'paymentMethod': {'data': {'type': 'PaymentMethod', 'id': '9'}}}},
    ]
    item_refs = []
    for item_id, product_id, quantity, price, canceled in items:
        included.append({'type': 'Item', 'id': item_id,
                         'attributes': {'quantity': quantity, 'price': price, 'canceled': canceled, 'cost': 400},
                         'relationships': {'product': {'data': {'type': 'Product', 'id': product_id}}}})
        item_refs.append({'type': 'Item', 'id': item_id})
    sale = {'type': 'Sale', 'id': sale_id,
            'attributes': {'createdAt': '2026-10-01T14:00:00Z', 'closedAt': closed, 'total': 3000,
                           'saleType': 'TAKEAWAY', 'saleState': 'CLOSED', 'people': 2, 'comment': 'sin azúcar'},
            'relationships': {'items': {'data': item_refs},
                              'waiter': {'data': {'type': 'User', 'id': '4'}},
                              'table': {'data': {'type': 'Table', 'id': '6'}},
                              'payments': {'data': [{'type': 'Payment', 'id': '11'}]}}}
    return {'data': [sale], 'included': included}


# ---- Parseo de Fudo ----

def test_parse_fudo_sale_reads_real_attribute_names():
    payload = _fudo_payload()
    fields = parse_fudo_sale(payload['data'][0], index_included(payload['included']))
    assert fields['tipo_venta'] == 'Para llevar'
    assert fields['estado'] == 'Cerrada'
    assert fields['camarero'] == 'Juan'
    assert fields['mesa'] == '12' and fields['sala'] == 'Vereda'
    assert fields['medio_pago'] == 'Efectivo'
    assert fields['comentario'] == 'sin azúcar'
    assert fields['personas'] == 2


def test_parse_fudo_items_skips_cancelled_and_computes_totals():
    payload = _fudo_payload(items=(('100', '7', 2, 1500, False), ('101', '8', 1, 900, True)))
    items = parse_fudo_items(payload['data'][0], index_included(payload['included']))
    assert len(items) == 1
    item = items[0]
    assert item['product_name'] == 'Cortado' and item['category_name'] == 'Cafetería'
    assert item['quantity'] == Decimal('2') and item['unit_price'] == Decimal('1500.00')
    assert item['total'] == Decimal('3000.00') and item['unit_cost'] == Decimal('400.00')
    assert item['external_id'] == '100' and item['fudo_product_id'] == '7'


# ---- Aplicar la sync ----

def test_new_fudo_sale_is_imported_with_items_linked_to_catalog(pos_app):
    cat = make_catalog()
    cat.taza.fudo_product_id = '7'
    db.session.commit()
    results = apply_fudo_sales(_fudo_payload())
    db.session.commit()
    assert results['imported'] == 1
    sale = Sale.query.filter_by(external_id=10).one()
    assert [(i.product_name, i.product_variant_id) for i in sale.items] == [('Cortado', cat.taza.id)]


def test_existing_sale_without_items_gets_them_without_update(pos_app):
    apply_fudo_sales(_fudo_payload(items=()))
    db.session.commit()
    sale = Sale.query.filter_by(external_id=10).one()
    sale.camarero = 'Editado a mano'
    db.session.commit()

    results = apply_fudo_sales(_fudo_payload(), update_existing=False)
    db.session.commit()
    assert results['skipped'] == 1 and results['items_backfilled'] == 1
    sale = Sale.query.filter_by(external_id=10).one()
    assert len(sale.items) == 1 and sale.camarero == 'Editado a mano'


def test_update_existing_replaces_items(pos_app):
    apply_fudo_sales(_fudo_payload())
    db.session.commit()
    results = apply_fudo_sales(_fudo_payload(items=(('100', '7', 3, 1500, False), ('102', '8', 1, 900, False))),
                               update_existing=True)
    db.session.commit()
    assert results['updated'] == 1
    sale = Sale.query.filter_by(external_id=10).one()
    assert sorted((i.external_id, float(i.quantity)) for i in sale.items) == [('100', 3.0), ('102', 1.0)]
    assert SaleItem.query.count() == 2


def test_broken_sale_does_not_stop_the_rest(pos_app):
    good = _fudo_payload(sale_id='20')
    bad = {'type': 'Sale', 'id': 'no-numero', 'attributes': {}}
    results = apply_fudo_sales({'data': [bad] + good['data'], 'included': good['included']})
    db.session.commit()
    assert results['imported'] == 1 and len(results['errors']) == 1
    assert Sale.query.filter_by(external_id=20).count() == 1


# ---- POS ----

def test_pos_close_projects_items_and_reopen_removes_them(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = sale_service.open_sale(cashier, 'salon', table_id=t1.id, people=2)
    sale_service.add_item(cashier, sale.id, cat.unidad.id, quantity=3)  # 2700
    sale_service.confirm_batch(cashier, sale.id)
    sale = sale_service.request_bill(cashier, sale.id)
    sale = payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 2700)

    row = db.session.get(Sale, sale.sale_id)
    assert [(i.product_name, i.variant_name, i.category_name, float(i.quantity), float(i.total))
            for i in row.items] == [('Medialuna', 'Unidad', 'Cafetería', 3.0, 2700.0)]


# ---- Reporte ----

def _sale(day, total, items):
    sale = Sale(fecha=day, creacion=datetime(day.year, day.month, day.day, 15), estado='Cerrada', total=total)
    for name, category, quantity, line_total in items:
        sale.items.append(SaleItem(product_name=name, category_name=category, quantity=quantity,
                                   unit_price=Decimal(line_total) / quantity, total=line_total))
    db.session.add(sale)


def test_products_report_aggregates_ranks_and_compares(pos_app):
    user = make_user('dueno@test.com', modules=('Reports',))
    # período anterior (septiembre): Cortado vendió 4000
    _sale(date(2026, 9, 15), 4000, [('Cortado', 'Cafetería', 2, 4000)])
    # octubre
    _sale(date(2026, 10, 1), 10000, [('Cortado', 'Cafetería', 4, 8000), ('Medialuna', 'Panadería', 2, 2000)])
    _sale(date(2026, 10, 2), 1000, [('Agua', None, 1, 1000)])
    _sale(date(2026, 10, 3), 5000, [])  # venta sin detalle
    db.session.commit()

    client = pos_app.test_client()
    response = client.get('/api/v1/reports/products?start_date=2026-10-01&end_date=2026-10-31',
                          headers=auth_headers(client, user))
    assert response.status_code == 200
    data = response.get_json()

    summary = data['summary']
    assert summary['unidades'] == pytest.approx(7)
    assert summary['facturacion'] == pytest.approx(11000)
    assert summary['productos'] == 3
    assert summary['ventas_con_detalle'] == 2 and summary['ventas_total'] == 3
    assert summary['cobertura_monto_pct'] == pytest.approx(68.8, abs=0.1)  # 11000 / 16000

    products = data['by_product']
    assert [p['producto'] for p in products] == ['Cortado', 'Medialuna', 'Agua']
    cortado = products[0]
    assert cortado['unidades'] == pytest.approx(4) and cortado['precio_promedio'] == pytest.approx(2000)
    assert cortado['porcentaje'] == pytest.approx(72.7, abs=0.1)
    assert cortado['facturacion_anterior'] == pytest.approx(4000) and cortado['variacion'] == pytest.approx(100)
    assert [p['clase'] for p in products] == ['A', 'B', 'C']
    assert products[2]['categoria'] == 'Sin categoría' and products[1]['variacion'] is None

    categories = {c['categoria']: c for c in data['by_category']}
    assert categories['Cafetería']['facturacion'] == pytest.approx(8000)
    assert categories['Panadería']['unidades'] == pytest.approx(2)


def test_products_report_requires_reports_module(pos_app):
    user = make_user('mozo@test.com', modules=('POS',))
    client = pos_app.test_client()
    response = client.get('/api/v1/reports/products', headers=auth_headers(client, user))
    assert response.status_code == 403
