from decimal import Decimal

from app.extensions import db
from app.models.menu import MenuCategory, MenuItem, MenuItemVariant
from app.services import cutover
from cash_helpers import make_register
from pos_helpers import auth_headers, make_catalog, make_user, pos_app  # noqa: F401
from app.services.pos import cash_service, payment_service, sale_service


def _admin(client):
    return auth_headers(client, make_user('admin@test.com', role='admin'))


def test_get_cutover_any_user(pos_app):
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('mozo@test.com', modules=('Camarero',)))
    data = client.get('/api/v1/system/cutover', headers=headers).get_json()
    assert data == {'catalog_in_galia': False, 'fudo_off': False, 'practice_mode': False}


def test_put_requires_admin(pos_app):
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('caja@test.com', modules=('POS',)))
    assert client.put('/api/v1/system/cutover', json={'practice_mode': True}, headers=headers).status_code == 403


def test_put_errors_use_pos_status(pos_app):
    client = pos_app.test_client()
    response = client.put('/api/v1/system/cutover', json={'fudo_off': True}, headers=_admin(client))
    assert response.status_code == 409 and response.get_json()['error'] == 'Primero pasá el catálogo a Galia'


def test_enable_catalog_links_menu(pos_app):
    client = pos_app.test_client()
    headers = _admin(client)
    cat = make_catalog()
    cat.unidad.fudo_product_id = '77'
    category = MenuCategory(name='Panadería', slug='panaderia')
    db.session.add(category)
    db.session.flush()
    item = MenuItem(category_id=category.id, name='Medialuna')
    item.variants = [MenuItemVariant(fudo_product_id='77', price=Decimal('900'), fudo_status='ok')]
    db.session.add(item)
    db.session.commit()
    response = client.put('/api/v1/system/cutover', json={'catalog_in_galia': True}, headers=headers)
    assert response.status_code == 200
    body = response.get_json()
    assert body['catalog_in_galia'] is True and body['link']['variants_linked'] == 1
    assert MenuItemVariant.query.one().product_variant_id == cat.unidad.id


def test_product_sync_blocked_with_catalog_in_galia(pos_app):
    client = pos_app.test_client()
    headers = _admin(client)
    cutover.get_settings().catalog_in_galia = True
    db.session.commit()
    response = client.post('/api/v1/products/sync', headers=headers)
    assert response.status_code == 409 and response.get_json()['error'] == 'El catálogo ya se maneja en Galia'


def test_catalog_in_galia_unlocks_fudo_fields(pos_app):
    client = pos_app.test_client()
    headers = _admin(client)
    cat = make_catalog()
    cat.unidad.fudo_product_id = '77'
    db.session.commit()
    url = f'/api/v1/products/{cat.medialuna.id}/variants/{cat.unidad.id}'
    assert client.put(url, json={'price': 1000}, headers=headers).status_code == 409  # Fudo todavía manda
    cutover.get_settings().catalog_in_galia = True
    db.session.commit()
    response = client.put(url, json={'price': 1000}, headers=headers)
    assert response.status_code == 200
    db.session.refresh(cat.unidad)
    assert cat.unidad.price == Decimal('1000')


def test_expenses_sync_blocked_when_fudo_off(pos_app):
    client = pos_app.test_client()
    headers = _admin(client)
    settings = cutover.get_settings()
    settings.catalog_in_galia = settings.fudo_off = True
    db.session.commit()
    response = client.post('/api/v1/fudo/sync/expenses?start_date=2026-09-01&end_date=2026-09-30', headers=headers)
    assert response.status_code == 409 and response.get_json()['error'] == 'Fudo está apagado'


def test_clear_practice_route(pos_app):
    client = pos_app.test_client()
    headers = _admin(client)
    admin = make_user('admin2@test.com', role='admin')
    cat = make_catalog()
    cutover.set_flags(admin, practice_mode=True)
    sale = sale_service.open_sale(admin, 'counter')
    sale_service.add_item(admin, sale.id, cat.unidad.id)
    payment_service.add_payment(admin, sale.id, cat.efectivo.id, 900)
    assert client.post('/api/v1/system/cutover/clear-practice', headers=headers).status_code == 409  # modo prendido
    assert client.put('/api/v1/system/cutover', json={'practice_mode': False}, headers=headers).status_code == 200
    response = client.post('/api/v1/system/cutover/clear-practice', headers=headers)
    assert response.status_code == 200 and response.get_json() == {'sales': 1, 'cash_sessions': 0}
