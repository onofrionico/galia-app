"""Corrección única de la carta: devuelve Cafetería y Bebidas al grupo Cafetería.

El 2026-11-07 las categorías Cafetería y Bebidas se pasaron por error al grupo Pastelería
desde el admin, y la carta se publicó así. Este script, que corre en build.sh, las vuelve a
poner en Cafetería, en el orden Cafetería, Bebidas, Licuados, y republica.

Corre una sola vez: deja la marca FLAG en menu_settings y desde ahí no hace nada, aunque el
admin vuelva a mover las categorías. Solo mueve una categoría si sigue en Pastelería (el
estado roto). Si había otros cambios sin publicar, corrige pero no publica, para no sacar a
la luz borradores ajenos.

Uso (desde backend/): python scripts/fix_carta_cafeteria.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.extensions import db  # noqa: E402
from app.models.menu import MenuCategory, MenuGroup, MenuSetting  # noqa: E402
from app.services import menu_publish_service  # noqa: E402

FLAG = 'fix_carta_cafeteria_2026_11'
CAFETERIA_ORDER = ['Cafetería', 'Bebidas', 'Licuados']
MOVED_BY_MISTAKE = ['Cafetería', 'Bebidas']


def fix(storage):
    """Aplica la corrección. Devuelve 'ya aplicado', 'sin cambios', 'publicado' o 'corregido sin publicar'."""
    if MenuSetting.get(FLAG):
        return 'ya aplicado'
    cafeteria = MenuGroup.query.filter_by(slug='cafeteria').first()
    pasteleria = MenuGroup.query.filter_by(slug='pasteleria').first()
    had_drafts = menu_publish_service.has_unpublished_changes()

    moved = False
    if cafeteria and pasteleria:
        for name in MOVED_BY_MISTAKE:
            category = MenuCategory.query.filter_by(name=name, group_id=pasteleria.id).first()
            if category is not None:
                category.group_id = cafeteria.id
                moved = True
        if moved:
            in_group = {c.name: c for c in MenuCategory.query.filter_by(group_id=cafeteria.id)}
            first = [in_group.pop(name) for name in CAFETERIA_ORDER if name in in_group]
            rest = sorted(in_group.values(), key=lambda c: (c.sort_order, c.id))
            for position, category in enumerate(first + rest):
                category.sort_order = position

    MenuSetting.set(FLAG, 'aplicado')
    db.session.commit()
    if not moved:
        return 'sin cambios'
    if had_drafts:
        return 'corregido sin publicar'
    menu_publish_service.publish(storage)
    return 'publicado'


def main():
    from app import create_app
    from app.utils.menu_storage import get_menu_storage

    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    app = create_app(os.environ.get('FLASK_ENV', 'production'))
    with app.app_context():
        result = fix(get_menu_storage())
        print(f'Carta, grupo Cafetería: {result}.')
        if result == 'corregido sin publicar':
            print('Había otros cambios sin publicar: revisarlos y publicar desde el admin.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
