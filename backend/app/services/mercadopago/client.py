"""Cliente REST de MercadoPago (Órdenes de Point, terminales, pagos). El armado y la lectura son puros."""
from datetime import datetime, timezone
from decimal import Decimal

import pytz
import requests

from app.services.mercadopago import MpRejected, MpUnavailable
from app.utils.timezone_utils import ARGENTINA_TZ

BASE_URL = 'https://api.mercadopago.com'
TIMEOUT = (5, 20)
ORDER_EXPIRATION = 'PT10M'
# Estado de la orden de MercadoPago -> estado de Galia.
ORDER_STATUS_MAP = {'created': 'created', 'at_terminal': 'processing', 'processed': 'approved',
                    'canceled': 'canceled', 'expired': 'expired', 'failed': 'failed', 'refunded': 'approved',
                    'action_required': 'processing'}
APPROVED_PAYMENT = ('approved', 'processed', 'accredited', 'refunded')
REJECTED_PAYMENT = ('rejected', 'failed')
RAW_FIELDS = ('id', 'date_created', 'date_approved', 'status', 'status_detail', 'transaction_amount',
              'transaction_amount_refunded', 'currency_id', 'payment_type_id', 'payment_method_id',
              'operation_type', 'external_reference', 'description')


def money_str(value):
    return f'{Decimal(value).quantize(Decimal("0.01")):.2f}'


def _money(value):
    return Decimal(str(value)).quantize(Decimal('0.01')) if value not in (None, '') else None


def order_state(order):
    """Estado de Galia de una orden de Point: status, status_detail, mp_payment_id, approved_amount."""
    payments = ((order.get('transactions') or {}).get('payments') or [])
    payment = payments[0] if payments else {}
    status = ORDER_STATUS_MAP.get(order.get('status'), 'processing')
    payment_status = payment.get('status')
    if payment_status in REJECTED_PAYMENT:
        status = 'failed'
    elif payment_status in APPROVED_PAYMENT and status in ('processing', 'approved'):
        status = 'approved'
    detail = payment.get('status_detail') or order.get('status_detail')
    approved = status == 'approved'
    payment_id = payment.get('reference_id') or payment.get('id')
    return {'status': status, 'status_detail': detail,
            'mp_payment_id': str(payment_id) if approved and payment_id else None,
            'approved_amount': _money(payment.get('paid_amount') or payment.get('amount')) if approved else None}


def channel_of(payment):
    poi = ((payment.get('point_of_interaction') or {}).get('type') or '').upper()
    payment_type = payment.get('payment_type_id')
    if poi == 'POINT':
        return 'point'
    if poi in ('INSTORE', 'QR', 'OPENPLATFORM'):
        return 'qr'
    if payment_type == 'bank_transfer':
        return 'transfer'
    if payment_type in ('credit_card', 'debit_card', 'account_money', 'prepaid_card'):
        return 'link'
    return 'other'


def movement_fields(payment):
    """Campos de mp_movements a partir de un pago de la búsqueda. Sin datos personales del pagador."""
    created = datetime.fromisoformat(payment['date_created'])
    created_utc = created.astimezone(timezone.utc).replace(tzinfo=None)
    business_date = created.astimezone(ARGENTINA_TZ).date()
    details = payment.get('transaction_details') or {}
    reference = payment.get('external_reference') or None
    return {
        'mp_payment_id': str(payment['id']), 'date_created': created_utc, 'business_date': business_date,
        'amount': _money(payment.get('transaction_amount')) or Decimal('0.00'),
        'refunded_amount': _money(payment.get('transaction_amount_refunded')) or Decimal('0.00'),
        'net_amount': _money(details.get('net_received_amount')), 'currency': payment.get('currency_id'),
        'status': payment.get('status') or 'unknown', 'status_detail': payment.get('status_detail'),
        'channel': channel_of(payment), 'payment_type': payment.get('payment_type_id'),
        'payment_method': payment.get('payment_method_id'), 'description': (payment.get('description') or '')[:255],
        'external_reference': reference[:64] if reference else None,
        'payer_label': payment.get('payment_method_id'),
        'raw': {k: payment.get(k) for k in RAW_FIELDS},
    }


def _iso(moment_utc):
    return pytz.utc.localize(moment_utc).astimezone(ARGENTINA_TZ).isoformat(timespec='milliseconds')


class MpClient:
    def __init__(self, access_token):
        self.access_token = access_token

    def _request(self, method, path, idempotency_key=None, extra_headers=None, **kwargs):
        headers = {'Authorization': f'Bearer {self.access_token}', 'Content-Type': 'application/json'}
        if idempotency_key:
            headers['X-Idempotency-Key'] = idempotency_key
        headers.update(extra_headers or {})
        try:
            response = requests.request(method, f'{BASE_URL}{path}', headers=headers, timeout=TIMEOUT, **kwargs)
        except requests.RequestException as exc:
            raise MpUnavailable(str(exc))
        if response.status_code >= 500:
            raise MpUnavailable(f'{response.status_code} {response.text[:200]}')
        try:
            data = response.json() if response.content else {}
        except ValueError:
            data = {}
        if response.status_code >= 400:
            errors = data.get('errors') or [{}]
            raise MpRejected(response.status_code, errors[0].get('code') or data.get('error') or '',
                             errors[0].get('message') or data.get('message') or response.text[:200])
        return data

    def me(self):
        return self._request('GET', '/users/me')

    def list_terminals(self):
        data = self._request('GET', '/terminals/v1/list', params={'limit': 50})
        return (data.get('data') or {}).get('terminals') or []

    def set_pdv_mode(self, terminal_id):
        return self._request('PATCH', '/terminals/v1/setup',
                             json={'terminals': [{'id': terminal_id, 'operating_mode': 'PDV'}]})

    def create_order(self, terminal_id, amount, external_reference, idempotency_key):
        body = {'type': 'point', 'external_reference': external_reference, 'expiration_time': ORDER_EXPIRATION,
                'transactions': {'payments': [{'amount': money_str(amount)}]},
                'config': {'point': {'terminal_id': terminal_id, 'print_on_terminal': 'no_ticket'}}}
        return self._request('POST', '/v1/orders', idempotency_key=idempotency_key, json=body)

    def get_order(self, order_id):
        return self._request('GET', f'/v1/orders/{order_id}')

    def cancel_order(self, order_id, at_terminal=False):
        extra = {'x-allow-cancelable-status': 'at_terminal'} if at_terminal else None
        return self._request('POST', f'/v1/orders/{order_id}/cancel', idempotency_key=f'cancel-{order_id}',
                             extra_headers=extra)

    def refund_order(self, order_id, idempotency_key):
        return self._request('POST', f'/v1/orders/{order_id}/refund', idempotency_key=idempotency_key)

    def search_payments(self, begin_utc, end_utc, offset=0):
        return self._request('GET', '/v1/payments/search', params={
            'range': 'date_created', 'begin_date': _iso(begin_utc), 'end_date': _iso(end_utc),
            'sort': 'date_created', 'criteria': 'asc', 'limit': 50, 'offset': offset})
