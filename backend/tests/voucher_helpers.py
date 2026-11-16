"""Fábricas compartidas por los tests de vouchers."""
from datetime import timedelta
from decimal import Decimal

from app.extensions import db
from app.models.vouchers import Voucher, VoucherBatch
from app.services.pos import sale_service
from app.services.vouchers.codes import generate_code
from app.utils.timezone_utils import get_current_date_argentina
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


def make_batch(amount='1000', quantity=3, expires_at=None, min_sale_amount=None, name='Sorteo Instagram',
               created_by=None):
    """Tanda con `quantity` vouchers, insertada directo (sin pasar por el servicio)."""
    if created_by is None:
        created_by = make_user(f'admin-{name}-{quantity}@test.com', role='admin').id
    batch = VoucherBatch(
        name=name, amount=Decimal(amount), quantity=quantity, created_by=created_by,
        expires_at=expires_at or get_current_date_argentina() + timedelta(days=30),
        min_sale_amount=Decimal(min_sale_amount) if min_sale_amount is not None else None)
    db.session.add(batch)
    db.session.flush()
    for _ in range(quantity):
        db.session.add(Voucher(batch_id=batch.id, code=generate_code()))
    db.session.commit()
    return batch


def open_sale(user, catalog, quantity=3):
    """Venta de mostrador con `quantity` medialunas (900 c/u) confirmadas."""
    sale = sale_service.open_sale(user, 'counter')
    sale_service.add_item(user, sale.id, catalog.unidad.id, quantity=quantity)
    sale_service.confirm_batch(user, sale.id)
    return sale
