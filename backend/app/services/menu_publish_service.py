import copy
import hashlib
import json
import logging
import os
from datetime import datetime

from app.extensions import db
from app.models.menu import MenuCategory, MenuItem, MenuTag, MenuSetting
from app.utils.menu_storage import public_url

logger = logging.getLogger(__name__)

SNAPSHOT_VERSION = 1


def _price(value):
    number = float(value)
    return int(number) if number.is_integer() else number


def _build(image_url):
    """Arma el contenido de la carta usando `image_url(image_key)` para las fotos."""
    categories = []
    used_tags = set()
    visible_categories = (
        MenuCategory.query.filter_by(is_visible=True)
        .order_by(MenuCategory.sort_order, MenuCategory.id)
        .all()
    )
    for category in visible_categories:
        items = []
        for item in category.items:
            if not item.is_visible:
                continue
            tag_slugs = sorted(tag.slug for tag in item.tags)
            used_tags.update(tag_slugs)
            items.append({
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'image': image_url(item.image_key),
                'featured': bool(item.is_featured),
                'tags': tag_slugs,
                'variants': [{'label': v.label, 'price': _price(v.price)} for v in item.variants],
            })
        if items:
            categories.append({
                'slug': category.slug,
                'name': category.name,
                'description': category.description,
                'items': items,
            })

    tags = [
        {'slug': tag.slug, 'name': tag.name, 'color': tag.color}
        for tag in MenuTag.query.order_by(MenuTag.name, MenuTag.id).all()
        if tag.slug in used_tags
    ]
    return {
        'version': SNAPSHOT_VERSION,
        'settings': {
            'footer_text': MenuSetting.get('footer_text', '') or '',
            'instagram': MenuSetting.get('instagram', '') or '',
        },
        'tags': tags,
        'categories': categories,
    }


def build_snapshot():
    """Arma el contenido público de la carta (sin `published_at`)."""
    return _build(public_url)


def _hash_snapshot():
    """Snapshot con la clave cruda de la imagen: el hash no depende de MENU_PUBLIC_BASE_URL."""
    return _build(lambda key: key)


def snapshot_hash(snapshot):
    encoded = json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def structure_hash():
    """Hash del snapshot ignorando precios: detecta cambios estructurales (no sólo de precio)."""
    snapshot = copy.deepcopy(_hash_snapshot())
    for category in snapshot['categories']:
        for item in category['items']:
            for variant in item.get('variants', []):
                variant.pop('price', None)
    return snapshot_hash(snapshot)


def has_unpublished_changes():
    return MenuSetting.get('last_published_hash') != snapshot_hash(_hash_snapshot())


def publish(storage):
    snapshot = build_snapshot()
    if not os.getenv('MENU_PUBLIC_BASE_URL', '').strip() and any(
        item['image'] for category in snapshot['categories'] for item in category['items']
    ):
        logger.warning('MENU_PUBLIC_BASE_URL no está configurada: las fotos de la carta tendrán URLs relativas')
    published_at = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    body = json.dumps({**snapshot, 'published_at': published_at}, ensure_ascii=False).encode('utf-8')
    storage.put('menu.json', body, 'application/json; charset=utf-8', 'public, max-age=60')

    MenuSetting.set('last_published_hash', snapshot_hash(_hash_snapshot()))
    MenuSetting.set('last_published_at', published_at)
    db.session.commit()

    try:
        _delete_orphan_images(storage)
    except Exception:
        logger.exception('No se pudieron borrar imágenes huérfanas de la carta')
    return {'published_at': published_at}


def _delete_orphan_images(storage):
    referenced = {
        key for (key,) in db.session.query(MenuItem.image_key).filter(MenuItem.image_key.isnot(None))
    }
    for key in storage.list('images/'):
        if key not in referenced:
            storage.delete(key)
