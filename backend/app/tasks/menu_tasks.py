"""Sincroniza precios de la carta desde Fudo y republica si corresponde.

Uso (cron de Render): cd backend && python -m app.tasks.menu_tasks
"""
import logging

from app.services import cutover, menu_catalog_sync, menu_publish_service, menu_sync_service

logger = logging.getLogger(__name__)


def sync_and_publish(client, storage):
    had_drafts = menu_publish_service.has_unpublished_changes()
    structure_before = menu_publish_service.structure_hash()
    if cutover.catalog_in_galia():
        stats = menu_catalog_sync.sync_from_catalog()
    else:
        stats = menu_sync_service.sync_fudo_products(client)
    structure_changed = menu_publish_service.structure_hash() != structure_before
    published = False
    if stats['price_changes'] and not had_drafts and not structure_changed:
        menu_publish_service.publish(storage)
        published = True
    return {**stats, 'published': published, 'structure_changed': structure_changed}


if __name__ == '__main__':
    import os

    from app import create_app
    from app.utils.fudo_client import FudoClient
    from app.utils.menu_storage import get_menu_storage

    logging.basicConfig(level=logging.INFO)
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    with app.app_context():
        client = None if cutover.catalog_in_galia() else FudoClient()  # con el catálogo en Galia no se usa Fudo
        logger.info('Sync de carta: %s', sync_and_publish(client, get_menu_storage()))
