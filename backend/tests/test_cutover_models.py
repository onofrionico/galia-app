from datetime import date
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import FudoImportMonth, OperationSettings
from app.services import cutover
from app.services.pos import cash_service, sale_service
from app.services.pos.errors import PosError
from cash_helpers import make_register
from pos_helpers import make_catalog, make_user, pos_app  # noqa: F401


def test_settings_singleton_defaults(pos_app):
    first = cutover.get_settings()
    second = cutover.get_settings()
    assert first.id == second.id == 1
    assert OperationSettings.query.count() == 1
    assert (cutover.catalog_in_galia(), cutover.fudo_off(), cutover.practice_mode()) == (False, False, False)


def test_require_fudo_on_and_catalog(pos_app):
    cutover.require_fudo_on()
    cutover.require_fudo_catalog()
    settings = cutover.get_settings()
    settings.fudo_off = True
    settings.catalog_in_galia = True
    db.session.commit()
    with pytest.raises(PosError) as error:
        cutover.require_fudo_on()
    assert error.value.status == 409 and error.value.message == 'Fudo está apagado'
    with pytest.raises(PosError) as error:
        cutover.require_fudo_catalog()
    assert error.value.message == 'El catálogo ya se maneja en Galia'


def test_month_matches(pos_app):
    month = FudoImportMonth(month=date(2026, 9, 1), status='done', fudo_count=3, galia_count=3,
                            fudo_total=Decimal('100.00'), galia_total=Decimal('100.00'), changed=0)
    assert month.matches is True
    month.galia_total = Decimal('90.00')
    assert month.matches is False


def test_practice_flags_default_false(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    make_catalog()
    register = make_register()
    session = cash_service.open_session(user, register.id, 0)
    sale = sale_service.open_sale(user, 'counter')
    assert session.is_practice is False and sale.is_practice is False
