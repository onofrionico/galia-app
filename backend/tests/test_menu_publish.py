import json
from decimal import Decimal

from app.extensions import db
from app.models.menu import MenuCategory, MenuGroup, MenuItem, MenuItemVariant, MenuTag, MenuSetting
from app.services.menu_publish_service import build_snapshot, has_unpublished_changes, publish


def _seed():
    tag = MenuTag(name='Sin TACC', slug='sin-tacc', color='#7FA34A')
    unused_tag = MenuTag(name='Vegano', slug='vegano', color='#000000')
    cafes = MenuCategory(name='Cafés', slug='cafes', sort_order=1, description='Contanos si lo preferís con azúcar')
    tortas = MenuCategory(name='Tortas', slug='tortas', sort_order=0)
    hidden = MenuCategory(name='Oculta', slug='oculta', sort_order=2, is_visible=False)
    empty = MenuCategory(name='Vacía', slug='vacia', sort_order=3)
    db.session.add_all([tag, unused_tag, cafes, tortas, hidden, empty])
    db.session.flush()

    latte = MenuItem(category_id=cafes.id, name='Latte', sort_order=0, is_featured=True, tags=[tag], image_key='images/latte.webp')
    latte.variants = [MenuItemVariant(price=Decimal('6900'))]
    secret = MenuItem(category_id=cafes.id, name='Secreto', sort_order=1, is_visible=False)
    secret.variants = [MenuItemVariant(price=Decimal('1'))]
    torta = MenuItem(category_id=tortas.id, name='Torta Galia', description='Masa de nuez')
    torta.variants = [
        MenuItemVariant(label='Porción', price=Decimal('11200'), sort_order=0),
        MenuItemVariant(label='Entera', price=Decimal('12600.50'), sort_order=1),
    ]
    in_hidden = MenuItem(category_id=hidden.id, name='No se ve')
    db.session.add_all([latte, secret, torta, in_hidden])
    MenuSetting.set('footer_text', '¡Que disfrutes tu estadía!')
    db.session.commit()


def test_build_snapshot_shape(menu_app):
    _seed()
    snapshot = build_snapshot()

    assert snapshot['version'] == 2
    assert snapshot['settings'] == {'footer_text': '¡Que disfrutes tu estadía!', 'instagram': ''}
    assert snapshot['tags'] == [{'slug': 'sin-tacc', 'name': 'Sin TACC', 'color': '#7FA34A'}]
    categories = snapshot['groups'][0]['categories']
    assert [c['slug'] for c in categories] == ['tortas', 'cafes']

    tortas, cafes = categories
    assert tortas['items'][0]['variants'] == [
        {'label': 'Porción', 'price': 11200},
        {'label': 'Entera', 'price': 12600.5},
    ]
    assert cafes['description'] == 'Contanos si lo preferís con azúcar'
    assert [i['name'] for i in cafes['items']] == ['Latte']
    latte = cafes['items'][0]
    assert latte['featured'] is True
    assert latte['tags'] == ['sin-tacc']
    assert latte['image'] == 'https://cdn.test/menu/images/latte.webp'
    assert 'published_at' not in snapshot


def test_publish_uploads_json_and_clears_pending_flag(menu_app, storage):
    _seed()
    assert has_unpublished_changes() is True

    result = publish(storage)

    stored = storage.objects['menu.json']
    assert stored['content_type'] == 'application/json; charset=utf-8'
    assert stored['cache_control'] == 'public, max-age=60'
    payload = json.loads(stored['body'].decode('utf-8'))
    assert payload['published_at'] == result['published_at']
    assert MenuSetting.get('last_published_at') == result['published_at']
    assert has_unpublished_changes() is False


def test_changes_after_publish_are_detected(menu_app, storage):
    _seed()
    publish(storage)
    MenuItem.query.filter_by(name='Latte').one().name = 'Latte grande'
    db.session.commit()
    assert has_unpublished_changes() is True


def test_publish_deletes_orphan_images_only(menu_app, storage):
    _seed()
    storage.put('images/latte.webp', b'x', 'image/webp', 'c')
    storage.put('images/old.webp', b'x', 'image/webp', 'c')
    publish(storage)
    assert storage.list('images/') == ['images/latte.webp']


def test_publish_survives_image_cleanup_failure(menu_app, storage):
    _seed()

    def boom(prefix):
        raise RuntimeError('s3 down')

    storage.list = boom
    result = publish(storage)

    assert 'published_at' in result
    assert 'menu.json' in storage.objects


def test_hash_does_not_depend_on_public_base_url(menu_app, storage, monkeypatch):
    _seed()
    monkeypatch.setenv('MENU_PUBLIC_BASE_URL', 'https://a.test/menu')
    publish(storage)
    monkeypatch.setenv('MENU_PUBLIC_BASE_URL', 'https://b.test/menu')
    assert has_unpublished_changes() is False

    payload = json.loads(storage.objects['menu.json']['body'].decode('utf-8'))
    images = [i['image'] for g in payload['groups'] for c in g['categories'] for i in c['items'] if i['image']]
    assert images == ['https://a.test/menu/images/latte.webp']


def test_publish_warns_when_base_url_empty_with_images(menu_app, storage, monkeypatch, caplog):
    _seed()
    monkeypatch.setenv('MENU_PUBLIC_BASE_URL', '')
    with caplog.at_level('WARNING'):
        publish(storage)
    assert 'MENU_PUBLIC_BASE_URL' in caplog.text


def test_snapshot_without_groups_is_single_untitled_group(menu_app):
    _seed()
    snapshot = build_snapshot()
    assert snapshot['version'] == 2
    assert [g['slug'] for g in snapshot['groups']] == ['_carta']
    assert snapshot['groups'][0]['name'] is None
    assert [c['slug'] for c in snapshot['groups'][0]['categories']] == ['tortas', 'cafes']
    assert 'categories' not in snapshot


def test_snapshot_groups_order_otros_and_empty_groups(menu_app):
    _seed()
    dulces = MenuGroup(name='Dulces', slug='dulces', sort_order=0)
    vacio = MenuGroup(name='Vacío', slug='vacio', sort_order=1)
    db.session.add_all([dulces, vacio])
    db.session.flush()
    MenuCategory.query.filter_by(slug='tortas').one().group_id = dulces.id
    MenuCategory.query.filter_by(slug='cafes').one().show_title = False
    db.session.commit()

    groups = build_snapshot()['groups']
    assert [(g['slug'], g['name']) for g in groups] == [('dulces', 'Dulces'), ('_otros', 'Otros')]
    assert groups[1]['categories'][0]['show_title'] is False
