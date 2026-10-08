"""Sincroniza precios de la carta desde Fudo y republica si corresponde.

Uso (cron de Render): cd backend && python -m app.tasks.menu_tasks
"""
import logging

from app.services import menu_publish_service, menu_sync_service

logger = logging.getLogger(__name__)


def sync_and_publish(client, storage):
    had_drafts = menu_publish_service.has_unpublished_changes()
    stats = menu_sync_service.sync_fudo_products(client)
    published = False
    if stats['price_changes'] and not had_drafts:
        menu_publish_service.publish(storage)
        published = True
    return {**stats, 'published': published}


if __name__ == '__main__':
    import os

    from app import create_app
    from app.utils.fudo_client import FudoClient
    from app.utils.menu_storage import get_menu_storage

    logging.basicConfig(level=logging.INFO)
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    with app.app_context():
        logger.info('Sync de carta: %s', sync_and_publish(FudoClient(), get_menu_storage()))
