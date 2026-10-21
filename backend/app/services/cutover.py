"""Interruptores del corte con Fudo: catálogo en Galia, Fudo apagado y modo práctica."""
from app.extensions import db
from app.models.operation_settings import SETTINGS_ID, OperationSettings
from app.services.pos.errors import PosError


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
