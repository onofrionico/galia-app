import json

from app.models.menu import MenuCategory, MenuItem, MenuItemVariant, MenuSetting, MenuTag
from app.services.menu_publish_service import build_snapshot
from seed_menu import SEED_PATH, seed


def _load_seed():
    with open(SEED_PATH, encoding='utf-8') as seed_file:
        return json.load(seed_file)


def test_seed_loads_full_menu(menu_app):
    seed(_load_seed())

    assert MenuCategory.query.count() == 19
    assert MenuItem.query.count() == 124
    assert MenuTag.query.count() == 4

    prices = [variant.price for variant in MenuItemVariant.query.all()]
    assert prices, 'seed produced no variants'
    assert all(price > 0 for price in prices)


def test_seed_preserves_category_order(menu_app):
    seed(_load_seed())

    categories = MenuCategory.query.order_by(MenuCategory.sort_order).all()
    assert categories[0].name == 'Cafetería'
    assert [c.sort_order for c in categories] == list(range(19))


def test_seed_assigns_tags_to_items(menu_app):
    seed(_load_seed())

    torta = MenuItem.query.filter_by(name='Torta Galia').one()
    assert 'Recomendado' in [tag.name for tag in torta.tags]


def test_seed_sets_footer_text(menu_app):
    seed(_load_seed())

    footer = MenuSetting.get('footer_text')
    assert footer
    assert footer.startswith('¡Que disfrutes tu estadía!')


def test_build_snapshot_returns_seeded_categories(menu_app):
    seed(_load_seed())

    snapshot = build_snapshot()
    assert len(snapshot['categories']) == 19
