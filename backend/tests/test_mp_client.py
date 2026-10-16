import hashlib
import hmac
from decimal import Decimal

import pytest

from app.services import mercadopago
from app.services.mercadopago import client as mpc
from app.services.mercadopago import settings as mps
from app.services.mercadopago.fake import FakeMercadoPago
from app.services.mercadopago.webhook import verify_signature
from mp_helpers import configure_mp
from pos_helpers import pos_app  # noqa: F401


def _order(status, payment_status=None, detail=None, amount='1800.00'):
    payments = [] if payment_status is None else [
        {'id': 'PAY01', 'amount': amount, 'paid_amount': amount, 'status': payment_status,
         'status_detail': detail, 'reference_id': '987654'}]
    return {'id': 'ORD01', 'status': status, 'status_detail': detail, 'transactions': {'payments': payments}}


def test_order_state_mapping():
    assert mpc.order_state(_order('created'))['status'] == 'created'
    assert mpc.order_state(_order('at_terminal'))['status'] == 'processing'
    approved = mpc.order_state(_order('processed', 'processed', 'accredited'))
    assert approved == {'status': 'approved', 'status_detail': 'accredited', 'mp_payment_id': '987654',
                        'approved_amount': Decimal('1800.00')}
    assert mpc.order_state(_order('canceled'))['status'] == 'canceled'
    assert mpc.order_state(_order('expired'))['status'] == 'expired'
    rejected = mpc.order_state(_order('failed', 'rejected', 'cc_rejected_insufficient_amount'))
    assert rejected['status'] == 'failed' and rejected['status_detail'] == 'cc_rejected_insufficient_amount'
    assert mpc.order_state(_order('refunded', 'refunded'))['status'] == 'approved'
    assert mpc.order_state(_order('something_new'))['status'] == 'processing'


def test_money_and_channels():
    assert mpc.money_str(Decimal('1234.5')) == '1234.50'
    assert mpc.channel_of({'point_of_interaction': {'type': 'POINT'}}) == 'point'
    assert mpc.channel_of({'point_of_interaction': {'type': 'INSTORE'}, 'payment_type_id': 'account_money'}) == 'qr'
    assert mpc.channel_of({'payment_type_id': 'bank_transfer'}) == 'transfer'
    assert mpc.channel_of({'operation_type': 'regular_payment', 'payment_type_id': 'credit_card'}) == 'link'
    assert mpc.channel_of({'payment_type_id': 'ticket'}) == 'other'


def test_movement_fields():
    fields = mpc.movement_fields({
        'id': 123, 'date_created': '2026-10-15T01:30:00.000-03:00', 'transaction_amount': 1800,
        'transaction_amount_refunded': 0, 'transaction_details': {'net_received_amount': 1750.5},
        'currency_id': 'ARS', 'status': 'approved', 'status_detail': 'accredited', 'payment_type_id': 'debit_card',
        'payment_method_id': 'debvisa', 'description': 'Venta', 'external_reference': 'galia-venta-1-1',
        'point_of_interaction': {'type': 'POINT'}, 'payer': {'email': 'cliente@example.com',
                                                               'identification': {'number': '30123456'}}})
    assert fields['mp_payment_id'] == '123' and fields['amount'] == Decimal('1800.00')
    assert fields['business_date'].isoformat() == '2026-10-15' and fields['channel'] == 'point'
    assert fields['net_amount'] == Decimal('1750.50') and 'cliente' not in str(fields['raw'])
    assert fields['payer_label'] == 'debvisa'


def test_webhook_signature():
    secret, request_id, data_id, ts = 'whsec', 'req-1', 'ORD01ABC', '1704908010'
    manifest = f'id:{data_id.lower()};request-id:{request_id};ts:{ts};'
    digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    assert verify_signature(secret, f'ts={ts},v1={digest}', request_id, data_id) is True
    assert verify_signature(secret, f'ts={ts},v1={"0" * 64}', request_id, data_id) is False
    assert verify_signature(secret, None, request_id, data_id) is False
    assert verify_signature(None, f'ts={ts},v1={digest}', request_id, data_id) is False


def test_settings_encryption_and_missing(pos_app):
    settings = mps.get_or_create_settings()
    assert 'token de prueba' in mps.missing(settings)
    configure_mp()
    settings = mps.get_settings()
    assert mps.missing(settings) == [] and mps.access_token(settings) == 'TEST-TOKEN'
    assert 'TEST-TOKEN' not in str(mps.settings_to_dict(settings))
    pos_app.config['SECRET_KEY'] = 'otra'
    assert any('no se puede leer' in item for item in mps.missing(settings))


def test_fake_client_only_with_flag_and_sqlite(pos_app, monkeypatch):
    configure_mp()
    monkeypatch.setenv('MP_FAKE', '1')
    assert isinstance(mercadopago.get_client(mps.get_settings()), FakeMercadoPago)
    monkeypatch.delenv('MP_FAKE')
    assert isinstance(mercadopago.get_client(mps.get_settings()), mpc.MpClient)


def test_fake_order_lifecycle(pos_app):
    FakeMercadoPago.reset()
    fake = FakeMercadoPago()
    order = fake.create_order('T1', Decimal('100'), 'ref-1', 'key-1')
    assert fake.create_order('T1', Decimal('100'), 'ref-1', 'key-1')['id'] == order['id']  # idempotente
    assert mpc.order_state(fake.get_order(order['id']))['status'] == 'created'
    fake.simulate(order['id'], 'approved')
    state = mpc.order_state(fake.get_order(order['id']))
    assert state['status'] == 'approved' and state['approved_amount'] == Decimal('100.00')
    assert fake.search_payments(None, None)['results'][0]['external_reference'] == 'ref-1'
    fake.refund_order(order['id'], 'r-1')
    assert fake.get_order(order['id'])['status'] == 'refunded'
    movement = fake.search_payments(None, None)['results'][0]
    assert movement['status'] == 'refunded' and movement['transaction_amount_refunded'] == 100.0
    other = fake.create_order('T1', Decimal('5'), 'ref-2', 'key-2')
    fake.cancel_order(other['id'])
    assert fake.get_order(other['id'])['status'] == 'canceled'
    fake.fail_next('create')
    with pytest.raises(mercadopago.MpUnavailable):
        fake.create_order('T1', Decimal('5'), 'ref-3', 'key-3')
