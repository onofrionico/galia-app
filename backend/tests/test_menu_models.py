from decimal import Decimal

from app.extensions import db
from app.models.menu import MenuCategory, MenuItem, MenuItemVariant, MenuTag, MenuSetting, FudoProduct, MenuGroup


def _category(name='Cafés', slug='cafes', order=0):
    category = MenuCategory(name=name, slug=slug, sort_order=order)
    db.session.add(category)
    db.session.flush()
    return category


def test_items_are_ordered_and_serialized(menu_app):
    category = _category()
    tag = MenuTag(name='Sin TACC', slug='sin-tacc', color='#7FA34A')
    second = MenuItem(category_id=category.id, name='Capuchino', sort_order=1)
    first = MenuItem(category_id=category.id, name='Latte', sort_order=0, image_key='images/a.webp', tags=[tag])
    first.variants = [MenuItemVariant(label=None, price=Decimal('6900'), sort_order=0)]
    db.session.add_all([tag, second, first])
    db.session.commit()

    data = category.to_dict(include_items=True)
    assert [i['name'] for i in data['items']] == ['Latte', 'Capuchino']
    latte = data['items'][0]
    assert latte['image_url'] == 'https://cdn.test/menu/images/a.webp'
    assert latte['tag_ids'] == [tag.id]
    assert latte['variants'][0]['price'] == 6900.0
    assert latte['variants'][0]['fudo_product_id'] is None


def test_deleting_item_deletes_variants(menu_app):
    category = _category()
    item = MenuItem(category_id=category.id, name='Torta Galia')
    item.variants = [MenuItemVariant(label='Porción', price=11200), MenuItemVariant(label='Entera', price=12600)]
    db.session.add(item)
    db.session.commit()

    db.session.delete(item)
    db.session.commit()
    assert MenuItemVariant.query.count() == 0


def test_menu_setting_get_and_set(menu_app):
    assert MenuSetting.get('footer_text', 'default') == 'default'
    MenuSetting.set('footer_text', '¡Que disfrutes!')
    db.session.commit()
    MenuSetting.set('footer_text', 'Otro texto')
    db.session.commit()
    assert MenuSetting.get('footer_text') == 'Otro texto'
    assert MenuSetting.query.count() == 1


def test_fudo_product_to_dict(menu_app):
    product = FudoProduct(fudo_id='42', name='Latte Vainilla', price=Decimal('6900'), category_name='Cafetería', is_active=True)
    db.session.add(product)
    db.session.commit()
    assert product.to_dict() == {
        'fudo_id': '42', 'name': 'Latte Vainilla', 'price': 6900.0,
        'category_name': 'Cafetería', 'is_active': True, 'ignored': False,
        'fudo_category_id': None,
    }


def test_group_and_category_fields(menu_app):
    group = MenuGroup(name='Desayuno', slug='desayuno', sort_order=0)
    db.session.add(group)
    db.session.flush()
    category = MenuCategory(name='Cafetería', slug='cafeteria', fudo_category_id='10', group_id=group.id)
    db.session.add(category)
    db.session.commit()

    data = category.to_dict()
    assert data['fudo_category_id'] == '10'
    assert data['group_id'] == group.id
    assert data['show_title'] is True
    assert data['fudo_status'] is None
    assert group.to_dict() == {'id': group.id, 'name': 'Desayuno', 'slug': 'desayuno', 'sort_order': 0}


def test_deleting_group_leaves_categories_ungrouped(menu_app):
    group = MenuGroup(name='Bebidas', slug='bebidas')
    db.session.add(group)
    db.session.flush()
    category = MenuCategory(name='Licuados', slug='licuados', group_id=group.id)
    db.session.add(category)
    db.session.commit()

    db.session.delete(group)
    db.session.commit()
    assert db.session.get(MenuCategory, category.id).group_id is None


def test_item_reviewed_flag(menu_app):
    category = MenuCategory(name='X', slug='x')
    db.session.add(category)
    db.session.flush()
    item = MenuItem(category_id=category.id, name='Latte')
    db.session.add(item)
    db.session.commit()
    assert item.to_dict()['reviewed'] is False
