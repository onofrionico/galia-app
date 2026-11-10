"""Endpoints del pronóstico de producción, sus turnos y los componentes de productos."""
from app.extensions import db
from app.models import ProductionSettings
from pos_helpers import pos_app  # noqa: F401


def test_settings_get_creates_defaults(pos_app):
    settings = ProductionSettings.get()
    db.session.commit()
    assert settings.comparable_weeks == 4 and settings.holiday_window_months == 12
    ProductionSettings.get()
    db.session.commit()
    assert ProductionSettings.query.count() == 1


# ---- Pronóstico ----

from datetime import date, datetime, timedelta  # noqa: E402
from decimal import Decimal  # noqa: E402

from app.models import Holiday, ProductComponent, ProductVariant, Sale, SaleItem, SalesDayPart  # noqa: E402
from pos_helpers import auth_headers, make_catalog, make_user  # noqa: E402

TARGET = date(2026, 11, 14)  # sábado


def _day_parts():
    parts = [SalesDayPart(name=n, start_time=s, end_time=e, position=i)
             for i, (n, s, e) in enumerate([('Desayuno', datetime.min.time().replace(hour=8),
                                             datetime.min.time().replace(hour=12)),
                                            ('Almuerzo', datetime.min.time().replace(hour=12),
                                             datetime.min.time().replace(hour=16)),
                                            ('Merienda', datetime.min.time().replace(hour=16),
                                             datetime.min.time().replace(hour=20))])]
    db.session.add_all(parts)
    db.session.commit()
    return parts


def _sale(day, utc_hour, items, estado='Cerrada', closed=True):
    """Venta del `day` a la `utc_hour` (UTC). items: (variant | None, nombre, cantidad)."""
    moment = datetime(day.year, day.month, day.day, utc_hour)
    sale = Sale(fecha=day, creacion=moment, cerrada=moment if closed else None, estado=estado, total=0)
    for variant, name, quantity in items:
        sale.items.append(SaleItem(product_variant_id=variant.id if variant else None, product_name=name,
                                   variant_name=variant.name if variant else None, category_name='Cafetería',
                                   quantity=quantity, unit_price=1, total=quantity))
    db.session.add(sale)
    db.session.commit()
    return sale


def _get(pos_app, user, query=''):
    client = pos_app.test_client()
    return client.get(f'/api/v1/reports/production-forecast{query}', headers=auth_headers(client, user))


def _row(data, producto):
    return next(p for p in data['products'] if p['producto'] == producto)


def test_forecast_endpoint_shape_and_values(pos_app):
    user = make_user('dueno@test.com', modules=('Reports',))
    desayuno = _day_parts()[0]
    cat = make_catalog()
    _sale(TARGET - timedelta(days=7), 12, [(cat.unidad, 'Medialuna', 10)])   # 09:00 local
    _sale(TARGET - timedelta(days=14), 12, [(cat.unidad, 'Medialuna', 20)])
    response = _get(pos_app, user, f'?date={TARGET.isoformat()}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['date'] == '2026-11-14' and data['is_holiday'] is False
    assert data['based_on'] == ['2026-11-07', '2026-10-31']
    assert [p['name'] for p in data['day_parts']] == ['Desayuno', 'Almuerzo', 'Merienda']
    medialuna = _row(data, 'Medialuna')
    assert medialuna['total'] == 15.0 and medialuna['categoria'] == 'Cafetería'
    assert medialuna['por_turno'][str(desayuno.id)] == 15.0
    assert medialuna['semana']['5'] == 15.0
    assert data['coverage'] == {'ventas_con_detalle': 2, 'ventas_total': 2}


def test_forecast_excludes_cancelled_sales(pos_app):
    user = make_user('dueno@test.com', modules=('Reports',))
    _day_parts()
    cat = make_catalog()
    _sale(TARGET - timedelta(days=7), 12, [(cat.unidad, 'Medialuna', 10)])
    _sale(TARGET - timedelta(days=7), 13, [(cat.unidad, 'Medialuna', 99)], estado='Cancelada')
    assert _row(_get(pos_app, user, f'?date={TARGET}').get_json(), 'Medialuna')['total'] == 10.0


def test_sale_without_cerrada_uses_creacion(pos_app):
    user = make_user('dueno@test.com', modules=('Reports',))
    almuerzo = _day_parts()[1]
    cat = make_catalog()
    _sale(TARGET - timedelta(days=7), 18, [(cat.unidad, 'Medialuna', 3)], closed=False)  # 15:00 local
    medialuna = _row(_get(pos_app, user, f'?date={TARGET}').get_json(), 'Medialuna')
    assert medialuna['por_turno'][str(almuerzo.id)] == 3.0


def test_forecast_expands_components(pos_app):
    user = make_user('dueno@test.com', modules=('Reports',))
    _day_parts()
    cat = make_catalog()
    combo = ProductVariant(product_id=cat.cortado.id, name='Combo', price=Decimal('3000'), stock_quantity=0,
                           min_stock=0)
    db.session.add(combo)
    db.session.flush()
    db.session.add(ProductComponent(variant_id=combo.id, component_variant_id=cat.unidad.id, quantity=2))
    db.session.commit()
    _sale(TARGET - timedelta(days=7), 12, [(combo, 'Combo Clásico', 1)])
    data = _get(pos_app, user, f'?date={TARGET}').get_json()
    medialuna = _row(data, 'Medialuna')
    assert medialuna['total'] == 2.0 and medialuna['desde_combos'] == 2.0
    assert medialuna['variante'] == 'Unidad'
    assert _row(data, 'Combo Clásico')['total'] == 1.0


def test_forecast_holiday_flag(pos_app):
    user = make_user('dueno@test.com', modules=('Reports',))
    _day_parts()
    db.session.add(Holiday(date=TARGET, name='Día X', type='national'))
    db.session.commit()
    data = _get(pos_app, user, f'?date={TARGET}').get_json()
    assert data['is_holiday'] is True and data['holiday_name'] == 'Día X'
    Holiday.query.filter_by(date=TARGET).one().type = 'special_event'
    db.session.commit()
    assert _get(pos_app, user, f'?date={TARGET}').get_json()['is_holiday'] is False


def test_forecast_without_comparable_days_is_empty(pos_app):
    user = make_user('dueno@test.com', modules=('Reports',))
    _day_parts()
    response = _get(pos_app, user, f'?date={TARGET}')
    assert response.status_code == 200
    assert response.get_json()['based_on'] == [] and response.get_json()['products'] == []


def test_forecast_defaults_to_tomorrow(pos_app):
    from app.utils.timezone_utils import get_current_date_argentina
    user = make_user('dueno@test.com', modules=('Reports',))
    data = _get(pos_app, user).get_json()
    assert data['date'] == (get_current_date_argentina() + timedelta(days=1)).isoformat()


def test_forecast_requires_reports_module(pos_app):
    user = make_user('mozo@test.com', modules=('POS',))
    assert _get(pos_app, user).status_code == 403


# ---- Configuración de turnos ----

SETTINGS_URL = '/api/v1/reports/production-settings'


def _client(pos_app, user):
    client = pos_app.test_client()
    return client, auth_headers(client, user)


def test_settings_put_updates_and_creates(pos_app):
    user = make_user('dueno@test.com', modules=('Reports',))
    parts = _day_parts()
    client, headers = _client(pos_app, user)
    body = client.get(SETTINGS_URL, headers=headers).get_json()
    assert body['comparable_weeks'] == 4 and len(body['day_parts']) == 3
    body['comparable_weeks'] = 6
    body['day_parts'][0]['start'] = '07:30'
    body['day_parts'].append({'name': 'Noche', 'start': '20:00', 'end': '22:00', 'is_active': True})
    response = client.put(SETTINGS_URL, json=body, headers=headers)
    assert response.status_code == 200, response.get_json()
    after = client.get(SETTINGS_URL, headers=headers).get_json()
    assert after['comparable_weeks'] == 6
    assert after['day_parts'][0]['start'] == '07:30'
    assert [p['name'] for p in after['day_parts']] == ['Desayuno', 'Almuerzo', 'Merienda', 'Noche']
    assert db.session.get(SalesDayPart, parts[0].id).updated_by == user.id
    assert ProductionSettings.get().updated_by == user.id


def test_overlapping_day_parts_rejected(pos_app):
    user = make_user('dueno@test.com', modules=('Reports',))
    _day_parts()
    client, headers = _client(pos_app, user)
    body = client.get(SETTINGS_URL, headers=headers).get_json()
    body['comparable_weeks'] = 8
    body['day_parts'][0]['end'] = '13:00'
    response = client.put(SETTINGS_URL, json=body, headers=headers)
    assert response.status_code == 400 and 'se superpone' in response.get_json()['error']
    after = client.get(SETTINGS_URL, headers=headers).get_json()
    assert after['day_parts'][0]['end'] == '12:00' and after['comparable_weeks'] == 4


def test_invalid_settings_rejected(pos_app):
    user = make_user('dueno@test.com', modules=('Reports',))
    _day_parts()
    client, headers = _client(pos_app, user)
    body = client.get(SETTINGS_URL, headers=headers).get_json()
    for change in ({'comparable_weeks': 0}, {'holiday_window_months': 99}):
        assert client.put(SETTINGS_URL, json={**body, **change}, headers=headers).status_code == 400
    bad = dict(body, day_parts=[dict(body['day_parts'][0], start='12:00', end='08:00')])
    assert client.put(SETTINGS_URL, json=bad, headers=headers).status_code == 400
    bad = dict(body, day_parts=[dict(body['day_parts'][0], name='  ')])
    assert client.put(SETTINGS_URL, json=bad, headers=headers).status_code == 400


def test_day_part_deactivated_not_deleted(pos_app):
    user = make_user('dueno@test.com', modules=('Reports',))
    merienda = _day_parts()[2]
    cat = make_catalog()
    _sale(TARGET - timedelta(days=7), 20, [(cat.unidad, 'Medialuna', 4)])  # 17:00 local
    client, headers = _client(pos_app, user)
    body = client.get(SETTINGS_URL, headers=headers).get_json()
    body['day_parts'][2]['is_active'] = False
    assert client.put(SETTINGS_URL, json=body, headers=headers).status_code == 200
    after = client.get(SETTINGS_URL, headers=headers).get_json()
    assert after['day_parts'][2]['is_active'] is False
    data = _get(pos_app, user, f'?date={TARGET}').get_json()
    assert merienda.id not in [p['id'] for p in data['day_parts']]
    assert _row(data, 'Medialuna')['fuera_de_turno'] == 4.0


def test_settings_require_reports_module(pos_app):
    user = make_user('mozo@test.com', modules=('POS',))
    client, headers = _client(pos_app, user)
    assert client.get(SETTINGS_URL, headers=headers).status_code == 403


# ---- Componentes ----

def _combo(cat):
    combo = ProductVariant(product_id=cat.cortado.id, name='Combo', price=Decimal('3000'), stock_quantity=0,
                           min_stock=0)
    db.session.add(combo)
    db.session.commit()
    return combo


def test_components_put_replaces_and_soft_deletes(pos_app):
    user = make_user('dueno@test.com', modules=('Products',))
    cat = make_catalog()
    combo = _combo(cat)
    client, headers = _client(pos_app, user)
    url = f'/api/v1/products/{cat.cortado.id}/components'
    both = {'components': [{'variant_id': combo.id, 'component_variant_id': cat.unidad.id, 'quantity': 2},
                           {'variant_id': combo.id, 'component_variant_id': cat.taza.id, 'quantity': 1}]}
    assert client.put(url, json=both, headers=headers).status_code == 200
    one = {'components': [{'variant_id': combo.id, 'component_variant_id': cat.unidad.id, 'quantity': 3}]}
    assert client.put(url, json=one, headers=headers).status_code == 200
    body = client.get(url, headers=headers).get_json()
    assert [(c['component_variant_id'], c['quantity']) for c in body['components']] == [(cat.unidad.id, 3.0)]
    assert body['components'][0]['component_label'] == 'Medialuna — Unidad'
    assert {v['name'] for v in body['variants']} == {'Taza', 'Combo'}
    removed = ProductComponent.query.filter_by(component_variant_id=cat.taza.id).one()
    assert removed.is_active is False and removed.updated_by == user.id


def test_component_cannot_be_itself(pos_app):
    user = make_user('dueno@test.com', modules=('Products',))
    cat = make_catalog()
    combo = _combo(cat)
    client, headers = _client(pos_app, user)
    url = f'/api/v1/products/{cat.cortado.id}/components'
    for item in ({'variant_id': combo.id, 'component_variant_id': combo.id, 'quantity': 1},
                 {'variant_id': cat.unidad.id, 'component_variant_id': cat.taza.id, 'quantity': 1},
                 {'variant_id': combo.id, 'component_variant_id': cat.unidad.id, 'quantity': 0},
                 {'variant_id': combo.id, 'component_variant_id': 9999, 'quantity': 1}):
        assert client.put(url, json={'components': [item]}, headers=headers).status_code == 400
    assert ProductComponent.query.count() == 0


def test_variant_search(pos_app):
    user = make_user('dueno@test.com', modules=('Products',))
    cat = make_catalog()
    client, headers = _client(pos_app, user)
    body = client.get('/api/v1/products/variants/search?q=medi', headers=headers).get_json()
    assert body == [{'id': cat.unidad.id, 'label': 'Medialuna — Unidad'}]


def test_components_require_products_module(pos_app):
    user = make_user('dueno@test.com', modules=('Reports',))
    cat = make_catalog()
    client, headers = _client(pos_app, user)
    assert client.get(f'/api/v1/products/{cat.cortado.id}/components', headers=headers).status_code == 403
