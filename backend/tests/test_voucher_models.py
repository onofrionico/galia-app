from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.pos import PosDiscount
from app.models.vouchers import Voucher
from app.services.pos import sale_service
from voucher_helpers import make_batch, make_catalog, make_user, open_sale, pos_app  # noqa: F401


def _discount(sale, user, voucher, cancelled=False):
    discount = PosDiscount(sale_id=sale.id, voucher_id=voucher.id, kind='amount', value=1000, amount=1000,
                           created_by=user.id, created_at=datetime.utcnow(),
                           cancelled_at=datetime.utcnow() if cancelled else None)
    db.session.add(discount)
    return discount


def _two_sales(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    return cashier, open_sale(cashier, cat), open_sale(cashier, cat)


def test_batch_and_vouchers_persist(pos_app):
    batch = make_batch(quantity=3)
    assert len(batch.vouchers) == 3
    assert all(len(v.code) == 10 for v in batch.vouchers)
    assert batch.vouchers[0].batch.name == 'Sorteo Instagram'


def test_voucher_code_is_unique(pos_app):
    batch = make_batch(quantity=1)
    db.session.add(Voucher(batch_id=batch.id, code=batch.vouchers[0].code))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_only_one_active_discount_per_voucher(pos_app):
    cashier, sale_a, sale_b = _two_sales(pos_app)
    voucher = make_batch(quantity=1).vouchers[0]
    _discount(sale_a, cashier, voucher)
    db.session.commit()
    _discount(sale_b, cashier, voucher)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_cancelled_discount_frees_voucher(pos_app):
    cashier, sale_a, sale_b = _two_sales(pos_app)
    voucher = make_batch(quantity=1).vouchers[0]
    _discount(sale_a, cashier, voucher, cancelled=True)
    db.session.commit()
    _discount(sale_b, cashier, voucher)
    db.session.commit()
    assert PosDiscount.query.filter_by(voucher_id=voucher.id, cancelled_at=None).count() == 1
