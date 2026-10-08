"""Carga inicial de la carta desde data/menu_seed.json.

Uso: cd backend && python seed_menu.py
No hace nada si ya hay categorías cargadas.
"""
import json
import os
from decimal import Decimal

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.menu import MenuCategory, MenuItem, MenuItemVariant, MenuSetting, MenuTag  # noqa: E402
from app.utils.slug import unique_slug  # noqa: E402

SEED_PATH = os.path.join(os.path.dirname(__file__), 'data', 'menu_seed.json')


def seed(data):
    tags = {}
    for tag_data in data.get('tags', []):
        tag = MenuTag(name=tag_data['name'], slug=unique_slug(MenuTag, tag_data['name']), color=tag_data['color'])
        db.session.add(tag)
        db.session.flush()
        tags[tag.name] = tag

    for category_order, category_data in enumerate(data['categories']):
        category = MenuCategory(
            name=category_data['name'],
            slug=unique_slug(MenuCategory, category_data['name']),
            description=category_data.get('description'),
            sort_order=category_order,
        )
        db.session.add(category)
        db.session.flush()
        for item_order, item_data in enumerate(category_data['items']):
            item = MenuItem(
                category_id=category.id,
                name=item_data['name'],
                description=item_data.get('description'),
                sort_order=item_order,
                tags=[tags[name] for name in item_data.get('tags', [])],
            )
            item.variants = [
                MenuItemVariant(label=v.get('label'), price=Decimal(str(v['price'])), sort_order=position)
                for position, v in enumerate(item_data['variants'])
            ]
            db.session.add(item)

    if data.get('footer_text'):
        MenuSetting.set('footer_text', data['footer_text'])
    db.session.commit()


if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    with app.app_context():
        if MenuCategory.query.first() is not None:
            print('La carta ya tiene categorías; no se cargó nada.')
        else:
            with open(SEED_PATH, encoding='utf-8') as seed_file:
                seed(json.load(seed_file))
            print(f'Carta cargada: {MenuCategory.query.count()} categorías, {MenuItem.query.count()} ítems.')
