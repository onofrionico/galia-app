"""Emite una Factura C y su nota de crédito reales en homologación de ARCA. Solo con credenciales de prueba.

Variables: ARCA_HOMO_CUIT, ARCA_HOMO_CERT (ruta al PEM), ARCA_HOMO_KEY (ruta a la clave), ARCA_HOMO_POS.
"""
import os
from datetime import date

import pytest

from app.extensions import db
from app.services.fiscal import invoice_service
from app.services.fiscal import settings as fs
from fiscal_helpers import closed_sale
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401
from print_helpers import make_printer

NEEDED = ('ARCA_HOMO_CUIT', 'ARCA_HOMO_CERT', 'ARCA_HOMO_KEY', 'ARCA_HOMO_POS')
pytestmark = pytest.mark.skipif(not all(os.getenv(n) for n in NEEDED),
                                reason='Sin credenciales de homologación de ARCA')


def test_real_invoice_and_credit_note_in_homologacion(pos_app):
    settings = fs.get_or_create_settings()
    settings.cuit = os.environ['ARCA_HOMO_CUIT']
    settings.business_name = 'Galia (prueba)'
    settings.address = 'Prueba 123'
    settings.activity_start = date(2020, 1, 1)
    settings.point_of_sale = int(os.environ['ARCA_HOMO_POS'])
    settings.environment = 'homologacion'
    with open(os.environ['ARCA_HOMO_KEY'], encoding='utf-8') as key_file:
        settings.homo_private_key = fs.encrypt_key(key_file.read())
    with open(os.environ['ARCA_HOMO_CERT'], encoding='utf-8') as cert_file:
        fs.save_certificate(settings, 'homologacion', cert_file.read())
    db.session.commit()
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    make_printer('Térmica caja', cashier=True)
    invoice = invoice_service.issue(user, closed_sale(user, cat, t1).id, None)
    assert invoice.status == 'authorized', invoice.error
    credit = invoice_service.cancel(user, invoice.id)
    assert credit.status == 'authorized', credit.error
