from datetime import date, datetime
from decimal import Decimal

from app.extensions import db
from app.models import Sale, SaleItem
from app.services import reports_products_compare as rpc
from app.services.pos import discount_service, payment_service, sale_service
from pos_helpers import auth_headers, make_catalog, make_user, pos_app  # noqa: F401

SEP, OCT = date(2026, 9, 1), date(2026, 10, 1)


def _sale(day, items, estado='Cerrada', source='fudo', external_id=None):
    sale = Sale(fecha=day, creacion=datetime(day.year, day.month, day.day, 12), estado=estado, total=0,
                source=source, external_id=external_id)
    db.session.add(sale)
    db.session.flush()
    for name, quantity, price, variant_id, variant_name in items:
        sale.items.append(SaleItem(product_name=name, variant_name=variant_name, category_name='Panadería',
                                   quantity=Decimal(str(quantity)), unit_price=Decimal(str(price)),
                                   total=Decimal(str(quantity * price)), product_variant_id=variant_id))
    db.session.commit()
    return sale


def _product(data, key):
    return next(p for p in data['products'] if p['key'] == key)


def test_compare_mixes_fudo_and_pos(pos_app):
    cat = make_catalog()
    _sale(date(2026, 9, 10), [('Medialuna', 3, 900, cat.unidad.id, 'Unidad')], external_id=1)
    _sale(date(2026, 10, 5), [('Medialuna', 2, 900, cat.unidad.id, 'Unidad')], source='galia')
    data = rpc.compare(SEP, OCT)
    assert data['months'] == ['2026-09', '2026-10']
    product = _product(data, f'p:{cat.medialuna.id}')
    assert product['a'] == {'quantity': '3.000', 'amount': '2700.00'}
    assert product['b'] == {'quantity': '2.000', 'amount': '1800.00'}
    assert len(data['products']) == 1 and data['totals']['b']['amount'] == '1800.00'


def test_compare_amount_is_without_sale_discount(pos_app):
    user = make_user('caja@test.com', modules=('POS', 'Descuentos'))
    cat = make_catalog()
    sale = sale_service.open_sale(user, 'counter')
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=2)
    discount_service.add_discount(user, sale.id, kind='percent', value=20, reason='Cliente habitual')
    sale = db.session.get(type(sale), sale.id)
    payment_service.add_payment(user, sale.id, cat.efectivo.id, sale.balance)
    projected = Sale.query.filter_by(source='galia').one()
    month = projected.fecha.replace(day=1)
    product = _product(rpc.compare(month, month), f'p:{cat.medialuna.id}')
    assert product['b']['amount'] == '1800.00'


def test_compare_excludes_cancelled(pos_app):
    cat = make_catalog()
    _sale(date(2026, 10, 5), [('Medialuna', 2, 900, cat.unidad.id, 'Unidad')], external_id=1)
    _sale(date(2026, 10, 6), [('Medialuna', 5, 900, cat.unidad.id, 'Unidad')], estado='Cancelada', external_id=2)
    assert _product(rpc.compare(SEP, OCT), f'p:{cat.medialuna.id}')['b']['quantity'] == '2.000'


def test_compare_unlinked_item_by_name(pos_app):
    _sale(date(2026, 10, 5), [('Torta vieja', 1, 5000, None, None)], external_id=1)
    product = _product(rpc.compare(SEP, OCT), 'n:Torta vieja')
    assert product['name'] == 'Torta vieja' and product['a'] == {'quantity': '0.000', 'amount': '0.00'}


def test_compare_variants_breakdown(pos_app):
    cat = make_catalog()
    from app.models import ProductVariant
    grande = ProductVariant(product_id=cat.cortado.id, name='Jarrito', price=Decimal('2500'), stock_quantity=0,
                            min_stock=0)
    db.session.add(grande)
    db.session.commit()
    _sale(date(2026, 10, 5), [('Cortado', 1, 2000, cat.taza.id, 'Taza'), ('Cortado', 2, 2500, grande.id, 'Jarrito')],
          external_id=1)
    product = _product(rpc.compare(SEP, OCT), f'p:{cat.cortado.id}')
    assert product['b'] == {'quantity': '3.000', 'amount': '7000.00'}
    assert {v['name']: v['b']['quantity'] for v in product['variants']} == {'Taza': '1.000', 'Jarrito': '2.000'}


def test_compare_daily(pos_app):
    cat = make_catalog()
    _sale(date(2026, 9, 10), [('Medialuna', 3, 900, cat.unidad.id, 'Unidad')], external_id=1)
    _sale(date(2026, 10, 10), [('Medialuna', 1, 900, cat.unidad.id, 'Unidad')], external_id=2)
    days = rpc.daily(f'p:{cat.medialuna.id}', SEP, OCT)['days']
    assert len(days) == 31
    tenth = days[9]
    assert tenth['day'] == 10 and tenth['a']['quantity'] == '3.000' and tenth['b']['quantity'] == '1.000'
    assert days[30]['a'] is None  # septiembre no tiene día 31


def test_compare_routes_permission_and_validation(pos_app):
    client = pos_app.test_client()
    reports = auth_headers(client, make_user('rep@test.com', modules=('Reports',)))
    other = auth_headers(client, make_user('caja@test.com', modules=('POS',)))
    url = '/api/v1/reports/products/compare?month_a=2026-09&month_b=2026-10'
    assert client.get(url, headers=other).status_code == 403
    assert client.get(url, headers=reports).status_code == 200
    assert client.get('/api/v1/reports/products/compare?month_a=2026-13&month_b=2026-10',
                      headers=reports).status_code == 400
    daily = client.get('/api/v1/reports/products/compare/daily?key=n:X&month_a=2026-09&month_b=2026-10',
                       headers=reports)
    assert daily.status_code == 200 and len(daily.get_json()['days']) == 31
