import json
from decimal import Decimal

from app.extensions import db
from app.models.menu import MenuCategory, MenuGroup, MenuItem, MenuItemVariant, MenuSetting
from app.services.menu_publish_service import has_unpublished_changes, publish
from scripts.fix_carta_cafeteria import FLAG, fix


def _category(name, slug, group, order):
    category = MenuCategory(name=name, slug=slug, group_id=group.id, sort_order=order)
    db.session.add(category)
    db.session.flush()
    item = MenuItem(category_id=category.id, name=f'Algo de {name}')
    item.variants = [MenuItemVariant(price=Decimal('1000'))]
    db.session.add(item)
    return category


def _broken_menu(storage):
    """Estado de producción del 2026-11-07: Cafetería y Bebidas cayeron en Pastelería."""
    cafeteria = MenuGroup(name='Cafetería', slug='cafeteria', sort_order=0)
    pasteleria = MenuGroup(name='Pastelería', slug='pasteleria', sort_order=1)
    db.session.add_all([cafeteria, pasteleria])
    db.session.flush()
    _category('Licuados', 'licuados', cafeteria, 2)
    _category('Pastelería', 'pasteleria-cat', pasteleria, 0)
    _category('Cafetería', 'cafeteria-cat', pasteleria, 8)
    _category('Bebidas', 'bebidas', pasteleria, 9)
    db.session.commit()
    publish(storage)
    return cafeteria, pasteleria


def _published_groups(storage):
    menu = json.loads(storage.objects['menu.json']['body'])
    return {g['name']: [c['name'] for c in g['categories']] for g in menu['groups']}


def test_moves_categories_back_and_publishes(menu_app):
    storage = menu_app.extensions['menu_storage']
    _broken_menu(storage)

    result = fix(storage)

    assert result == 'publicado'
    assert _published_groups(storage) == {
        'Cafetería': ['Cafetería', 'Bebidas', 'Licuados'],
        'Pastelería': ['Pastelería'],
    }
    assert not has_unpublished_changes()
    assert MenuSetting.get(FLAG)


def test_runs_only_once(menu_app):
    storage = menu_app.extensions['menu_storage']
    _, pasteleria = _broken_menu(storage)
    fix(storage)
    bebidas = MenuCategory.query.filter_by(name='Bebidas').one()
    bebidas.group_id = pasteleria.id  # una decisión posterior del admin
    db.session.commit()

    assert fix(storage) == 'ya aplicado'
    assert MenuCategory.query.filter_by(name='Bebidas').one().group_id == pasteleria.id


def test_does_not_touch_categories_already_moved_elsewhere(menu_app):
    storage = menu_app.extensions['menu_storage']
    cafeteria, _ = _broken_menu(storage)
    otro = MenuGroup(name='Bebidas frías', slug='bebidas-frias', sort_order=2)
    db.session.add(otro)
    db.session.flush()
    MenuCategory.query.filter_by(name='Bebidas').one().group_id = otro.id
    db.session.commit()
    publish(storage)

    fix(storage)

    assert MenuCategory.query.filter_by(name='Bebidas').one().group_id == otro.id
    assert MenuCategory.query.filter_by(name='Cafetería').one().group_id == cafeteria.id


def test_with_other_unpublished_changes_fixes_but_does_not_publish(menu_app):
    storage = menu_app.extensions['menu_storage']
    _broken_menu(storage)
    MenuItem.query.filter_by(name='Algo de Licuados').one().name = 'Borrador sin publicar'
    db.session.commit()
    before = storage.objects['menu.json']['body']

    assert fix(storage) == 'corregido sin publicar'

    assert storage.objects['menu.json']['body'] == before
    assert MenuCategory.query.filter_by(name='Cafetería').one().group.slug == 'cafeteria'


def test_missing_groups_is_a_no_op(menu_app):
    storage = menu_app.extensions['menu_storage']

    assert fix(storage) == 'sin cambios'
    assert MenuSetting.get(FLAG)
