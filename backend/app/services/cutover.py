"""Interruptores del corte con Fudo: catálogo en Galia, Fudo apagado y modo práctica."""
from datetime import datetime

from app.extensions import db
from app.models.operation_settings import SETTINGS_ID, OperationSettings
from app.services.pos.errors import PosError, forbidden


def get_settings():
    settings = db.session.get(OperationSettings, SETTINGS_ID)
    if settings is None:
        settings = OperationSettings(id=SETTINGS_ID, catalog_in_galia=False, fudo_off=False, practice_mode=False)
        db.session.add(settings)
        db.session.flush()
    return settings


def catalog_in_galia():
    return bool(get_settings().catalog_in_galia)


def fudo_off():
    return bool(get_settings().fudo_off)


def practice_mode():
    return bool(get_settings().practice_mode)


def require_fudo_on():
    if fudo_off():
        raise PosError('Fudo está apagado')


def require_fudo_catalog():
    if catalog_in_galia():
        raise PosError('El catálogo ya se maneja en Galia')


def _open_cash(practice):
    from app.models.pos import CashSession
    return CashSession.query.filter_by(status='open', is_practice=practice).first() is not None


def _open_sales(practice):
    from app.models.pos import PosSale
    return PosSale.query.filter(PosSale.status.in_(('open', 'billing')), PosSale.is_practice == practice).first() \
        is not None


def set_flags(user, catalog_in_galia=None, fudo_off=None, practice_mode=None):
    """Cambia los interruptores (solo admin). Valida las reglas antes de tocar nada."""
    if getattr(user, 'role', None) != 'admin':
        raise forbidden('Solo un administrador cambia los interruptores del corte')
    settings = get_settings()
    if practice_mode is not None and bool(practice_mode) != settings.practice_mode:
        if practice_mode:
            if _open_cash(False):
                raise PosError('Cerrá la caja antes de entrar en modo práctica')
            if _open_sales(False):
                raise PosError('Hay ventas reales abiertas')
        else:
            if _open_cash(True):
                raise PosError('Cerrá la caja de práctica antes de salir')
            if _open_sales(True):
                raise PosError('Hay ventas de práctica abiertas')
        settings.practice_mode = bool(practice_mode)
    link_menu = False
    if catalog_in_galia is not None and bool(catalog_in_galia) != settings.catalog_in_galia:
        if not catalog_in_galia and settings.fudo_off:
            raise PosError('Primero prendé Fudo')
        settings.catalog_in_galia = bool(catalog_in_galia)
        link_menu = settings.catalog_in_galia
    if fudo_off is not None and bool(fudo_off) != settings.fudo_off:
        if fudo_off and not settings.catalog_in_galia:
            raise PosError('Primero pasá el catálogo a Galia')
        settings.fudo_off = bool(fudo_off)
    settings.updated_at = datetime.utcnow()
    settings.updated_by = user.id
    link = None
    if link_menu:
        from app.services import menu_catalog_sync  # Task del catálogo: vincula la carta
        link = menu_catalog_sync.link_to_catalog()
    db.session.commit()
    settings.last_link = link
    return settings
