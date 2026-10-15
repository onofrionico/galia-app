import base64
from datetime import datetime, timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

from app.extensions import db
from app.models.pos import PrintJob, PrintPoint, QzSigningKey
from app.services.pos import payment_service, print_service, qz_signing, sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401
from print_helpers import make_printer, make_station


@pytest.fixture
def ctx(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    barra = make_station('Barra')
    cat.category.station_id = barra.id
    db.session.commit()
    bar_printer = make_printer('Térmica barra', station=barra, point='Caja')
    cashier = make_printer('Térmica caja', cashier=True, point='Caja', width=58)
    return user, cat, t1, barra, bar_printer, cashier


def _billed(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=2)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=2)
    sale_service.confirm_batch(user, sale.id)
    return sale_service.request_bill(user, sale.id)


def test_bill_and_receipt_go_to_cashier_printer(ctx):
    user, cat, t1, _barra, _bp, cashier = ctx
    sale = _billed(user, cat, t1)
    bill = print_service.print_bill(user, sale.id)
    assert bill.kind == 'bill' and bill.printer_id == cashier.id
    doc = bill.document
    assert doc['title'] == 'PRECUENTA' and doc['lines'][0]['amount'] == '1800.00'
    assert doc['totals'][-1] == {'label': 'TOTAL', 'amount': '1800.00'} and doc['footer'] == ['No válido como factura']
    assert 'Personas: 2' in doc['header']
    with pytest.raises(PosError) as error:
        print_service.print_receipt(user, sale.id)
    assert error.value.status == 409
    payment_service.add_payment(user, sale.id, cat.efectivo.id, 1800, tendered=2000)
    receipt = print_service.print_receipt(user, sale.id)
    labels = [t['label'] for t in receipt.document['totals']]
    assert receipt.document['title'] == 'TICKET' and labels[-2:] == ['Efectivo', 'Vuelto']
    assert receipt.document['totals'][-1]['amount'] == '200.00'


def test_bill_requires_confirmed_items_and_a_cashier_printer(ctx):
    user, cat, t1, _barra, _bp, cashier = ctx
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    with pytest.raises(PosError) as error:
        print_service.print_bill(user, sale.id)
    assert error.value.status == 409
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale_service.confirm_batch(user, sale.id)
    cashier.is_active = False
    db.session.commit()
    with pytest.raises(PosError) as error:
        print_service.print_bill(user, sale.id)
    assert error.value.status == 409 and error.value.message == 'No hay impresora de caja configurada'


def test_reprint_copies_with_mark_and_follows_current_printer(ctx):
    user, cat, t1, barra, bar_printer, _cashier = ctx
    _billed(user, cat, t1)
    order = PrintJob.query.filter_by(kind='order').one()
    bar_printer.is_active = False
    db.session.commit()
    with pytest.raises(PosError) as error:
        print_service.reprint(user, order.id)
    assert error.value.status == 409
    new_printer = make_printer('Térmica barra 2', station=barra, point='Caja')
    copy = print_service.reprint(user, order.id)
    assert copy.reprint_of == order.id and copy.printer_id == new_printer.id
    assert copy.document['header'][-1] == 'REIMPRESIÓN' and order.document['header'][-1] != 'REIMPRESIÓN'


def test_claim_filters_by_point_and_marks_printing(ctx):
    user, cat, t1, _barra, bar_printer, _cashier = ctx
    make_printer('Térmica oficina', cashier=False, point='Oficina')
    _billed(user, cat, t1)
    assert print_service.claim('Oficina') == []
    jobs = print_service.claim('Caja')
    assert [(j.kind, j.status, j.claimed_by) for j in jobs] == [('order', 'printing', 'Caja')]
    assert print_service.claim('Caja') == []
    assert db.session.get(PrintPoint, 'Caja').last_seen_at is not None
    done = print_service.mark_done(jobs[0].id)
    assert done.status == 'printed' and done.printed_at is not None


def test_failed_jobs_retry_until_max_then_wait_for_manual(ctx):
    user, cat, t1, _barra, _bp, _cashier = ctx
    _billed(user, cat, t1)
    job = print_service.claim('Caja')[0]
    for attempt in range(1, print_service.MAX_ATTEMPTS + 1):
        failed = print_service.mark_failed(job.id, 'Sin papel')
        assert failed.status == 'failed' and failed.attempts == attempt and failed.error == 'Sin papel'
        failed.failed_at = datetime.utcnow() - timedelta(seconds=20)
        db.session.commit()
        claimed = print_service.claim('Caja')
        if attempt < print_service.MAX_ATTEMPTS:
            assert [j.id for j in claimed] == [job.id]
        else:
            assert claimed == []
    retried = print_service.retry(job.id)
    assert retried.status == 'pending' and retried.attempts == 0
    marked = print_service.mark_printed(job.id)
    assert marked.status == 'printed' and marked.claimed_by == 'manual'
    with pytest.raises(PosError):
        print_service.retry(job.id)


def test_stale_printing_returns_to_queue(ctx):
    user, cat, t1, _barra, _bp, _cashier = ctx
    _billed(user, cat, t1)
    job = print_service.claim('Caja')[0]
    job.claimed_at = datetime.utcnow() - timedelta(seconds=61)
    db.session.commit()
    again = print_service.claim('Caja')
    assert [j.id for j in again] == [job.id]


def test_status_reports_problems_and_down_points(ctx):
    user, cat, t1, _barra, _bp, _cashier = ctx
    status = print_service.status()
    assert status == {'problems': [], 'points': [{'name': 'Caja', 'last_seen_at': None, 'down': True}],
                      'pending': 0}
    _billed(user, cat, t1)
    job = PrintJob.query.one()
    job.created_at = datetime.utcnow() - timedelta(seconds=31)
    db.session.commit()
    print_service.claim('Caja')
    status = print_service.status()
    assert [p['id'] for p in status['problems']] == [job.id] and status['pending'] == 1
    assert status['points'][0]['down'] is False
    assert status['problems'][0]['place'] == 'Mesa 1' and status['problems'][0]['station_name'] == 'Barra'


def test_test_print_and_print_points(ctx):
    user, _cat, _t1, _barra, bar_printer, cashier = ctx
    job = print_service.test_print(user, cashier.id)
    assert job.kind == 'test' and job.sale_id is None and job.document['title'] == 'PRUEBA'
    points = print_service.print_points()
    assert [p['name'] for p in points] == ['Caja']
    assert sorted(p['name'] for p in points[0]['printers']) == sorted([bar_printer.name, cashier.name])


def test_job_dict_with_printer_connection(ctx):
    user, cat, t1, _barra, bar_printer, _cashier = ctx
    _billed(user, cat, t1)
    job = print_service.claim('Caja')[0]
    data = print_service.job_to_dict(job, with_printer=True)
    assert data['printer'] == {'id': bar_printer.id, 'name': 'Térmica barra', 'connection': 'network',
                               'host': '192.168.0.50', 'port': 9100, 'os_name': None, 'paper_width': 80}
    assert data['document']['title'] == 'BARRA' and data['sale_number'] == 1


def _key_pair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'galia-test')])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(1).not_valid_before(datetime(2026, 1, 1)).not_valid_after(datetime(2036, 1, 1))
            .sign(key, hashes.SHA256()))
    key_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption()).decode()
    return cert, cert.public_bytes(serialization.Encoding.PEM).decode(), key_pem


def test_qz_keys_are_generated_once_and_persisted(pos_app, monkeypatch):
    monkeypatch.delenv('QZ_CERTIFICATE', raising=False)
    monkeypatch.delenv('QZ_PRIVATE_KEY', raising=False)
    cert_pem = qz_signing.qz_certificate()
    assert cert_pem.startswith('-----BEGIN CERTIFICATE-----')
    assert QzSigningKey.query.count() == 1
    db.session.expire_all()
    assert qz_signing.qz_certificate() == cert_pem
    cert = x509.load_pem_x509_certificate(cert_pem.encode())
    assert cert.not_valid_after.year >= datetime.utcnow().year + 9
    signature = base64.b64decode(qz_signing.sign_qz('mensaje de QZ'))
    cert.public_key().verify(signature, b'mensaje de QZ', padding.PKCS1v15(), hashes.SHA512())


def test_qz_env_keys_take_precedence(pos_app, monkeypatch):
    qz_signing.qz_certificate()  # ya hay un par generado en la base
    cert, cert_pem, key_pem = _key_pair()
    monkeypatch.setenv('QZ_CERTIFICATE', cert_pem.replace('\n', '\\n'))
    monkeypatch.setenv('QZ_PRIVATE_KEY', key_pem.replace('\n', '\\n'))
    assert qz_signing.qz_certificate() == cert_pem
    signature = base64.b64decode(qz_signing.sign_qz('mensaje de QZ'))
    cert.public_key().verify(signature, b'mensaje de QZ', padding.PKCS1v15(), hashes.SHA512())
