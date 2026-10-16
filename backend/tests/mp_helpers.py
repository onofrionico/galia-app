"""Fábricas compartidas por los tests de MercadoPago."""
from app.extensions import db
from app.models.pos import PaymentMethod
from app.services.mercadopago import settings as mp_settings
from app.services.pos import sale_service

TERMINAL = 'PAX_A910__SMARTPOS1'


def configure_mp(point_method=None):
    if point_method is None:
        point_method = PaymentMethod(name='MercadoPago Point', kind='card', position=9, is_mercadopago=True)
        db.session.add(point_method)
        db.session.flush()
    settings = mp_settings.get_or_create_settings()
    settings.environment = 'test'
    settings.set_token('test', mp_settings.encrypt('TEST-TOKEN'))
    settings.terminal_id = TERMINAL
    settings.webhook_secret = mp_settings.encrypt('whsec')
    settings.point_payment_method_id = point_method.id
    db.session.commit()
    return settings


def billing_sale(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=1)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=2)
    sale_service.confirm_batch(user, sale.id)
    return sale_service.request_bill(user, sale.id)
