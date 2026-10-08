from decimal import Decimal

from app.extensions import db
from app.models.menu import MenuCategory, MenuItem, MenuItemVariant


def test_update_item_with_missing_fudo_variant_keeps_link(menu_client, admin_headers):
    category = MenuCategory(name='Cafés', slug='cafes')
    db.session.add(category)
    db.session.flush()
    item = MenuItem(category_id=category.id, name='Latte')
    item.variants = [MenuItemVariant(price=Decimal('6900'), fudo_product_id='9', fudo_status='missing')]
    db.session.add(item)
    db.session.commit()

    response = menu_client.put(f'/api/v1/menu/items/{item.id}', headers=admin_headers, json={
        'name': 'Latte nuevo',
        'variants': [{'label': None, 'fudo_product_id': '9', 'price': None}],
    })
    data = response.get_json()
    assert response.status_code == 200, data
    assert data['name'] == 'Latte nuevo'
    variant = data['variants'][0]
    assert (variant['price'], variant['fudo_product_id'], variant['fudo_status']) == (6900.0, '9', 'missing')


def test_new_unknown_fudo_id_still_rejected_on_existing_item(menu_client, admin_headers):
    category = MenuCategory(name='Cafés', slug='cafes')
    db.session.add(category)
    db.session.flush()
    item = MenuItem(category_id=category.id, name='Latte')
    item.variants = [MenuItemVariant(price=Decimal('6900'))]
    db.session.add(item)
    db.session.commit()
    response = menu_client.put(f'/api/v1/menu/items/{item.id}', headers=admin_headers, json={
        'variants': [{'fudo_product_id': '404'}],
    })
    assert response.status_code == 400
