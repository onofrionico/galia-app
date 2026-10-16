"""MercadoPago de mentira para tests y el preview local (MP_FAKE=1 con SQLite). Nunca en producción."""
import itertools
import threading
from datetime import datetime, timezone
from decimal import Decimal

from app.services.mercadopago import MpRejected, MpUnavailable


class FakeMercadoPago:
    orders = {}
    payments = []
    by_key = {}
    failures = set()
    _ids = itertools.count(1)
    _lock = threading.Lock()

    @classmethod
    def reset(cls):
        with cls._lock:
            cls.orders, cls.payments, cls.by_key, cls.failures = {}, [], {}, set()

    @classmethod
    def fail_next(cls, kind):
        cls.failures.add(kind)

    def _maybe_fail(self, kind):
        if kind in self.failures:
            self.failures.discard(kind)
            raise MpUnavailable(f'{kind} (simulado)')

    def me(self):
        return {'id': 1, 'nickname': 'GALIA-PRUEBA'}

    def list_terminals(self):
        return [{'id': 'PAX_A910__SMARTPOS1', 'operating_mode': 'PDV'}]

    def set_pdv_mode(self, terminal_id):
        return {'terminals': [{'id': terminal_id, 'operating_mode': 'PDV'}]}

    def create_order(self, terminal_id, amount, external_reference, idempotency_key):
        self._maybe_fail('create')
        with self._lock:
            if idempotency_key in self.by_key:
                return dict(self.orders[self.by_key[idempotency_key]])
            order_id = f'ORD{next(self._ids):05d}'
            self.orders[order_id] = {'id': order_id, 'status': 'created', 'external_reference': external_reference,
                                     'terminal_id': terminal_id, 'transactions': {'payments': [
                                         {'id': f'PAY{order_id}', 'amount': f'{Decimal(amount):.2f}',
                                          'status': 'created'}]}}
            self.by_key[idempotency_key] = order_id
            return dict(self.orders[order_id])

    def get_order(self, order_id):
        self._maybe_fail('get')
        if order_id not in self.orders:
            raise MpRejected(404, 'order_not_found', 'Order not found')
        return dict(self.orders[order_id])

    def simulate(self, order_id, outcome, paid_amount=None):
        """Lo que haría el Point: approved | rejected | expired | processing."""
        with self._lock:
            order = self.orders[order_id]
            payment = order['transactions']['payments'][0]
            if outcome == 'processing':
                order['status'] = 'at_terminal'
            elif outcome == 'approved':
                order['status'] = 'processed'
                payment.update({'status': 'processed', 'status_detail': 'accredited',
                                'paid_amount': f'{Decimal(paid_amount or payment["amount"]):.2f}',
                                'reference_id': str(70000 + len(self.payments))})
                self.payments.append({
                    'id': int(payment['reference_id']),
                    'date_created': datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
                    'transaction_amount': float(Decimal(payment['paid_amount'])), 'status': 'approved',
                    'status_detail': 'accredited', 'payment_type_id': 'debit_card', 'payment_method_id': 'debvisa',
                    'external_reference': order['external_reference'], 'currency_id': 'ARS',
                    'point_of_interaction': {'type': 'POINT'}})
            elif outcome == 'rejected':
                order['status'] = 'failed'
                payment.update({'status': 'rejected', 'status_detail': 'cc_rejected_insufficient_amount'})
            elif outcome == 'expired':
                order['status'] = 'expired'

    def add_payment_movement(self, payment):
        with self._lock:
            self.payments.append(payment)

    def cancel_order(self, order_id, at_terminal=False):
        self._maybe_fail('cancel')
        order = self.orders[order_id]
        if order['status'] == 'at_terminal' and not at_terminal:
            raise MpRejected(409, 'cannot_cancel_order', 'Order cannot be canceled')
        if order['status'] not in ('created', 'at_terminal'):
            raise MpRejected(409, 'cannot_cancel_order', 'Order cannot be canceled')
        order['status'] = 'canceled'
        return dict(order)

    def refund_order(self, order_id, idempotency_key):
        self._maybe_fail('refund')
        order = self.orders[order_id]
        if order['status'] not in ('processed', 'refunded'):
            raise MpRejected(400, 'invalid_status', 'Order cannot be refunded')
        order['status'] = 'refunded'
        for payment in self.payments:  # como en MercadoPago: el pago queda devuelto
            if payment.get('external_reference') == order['external_reference']:
                payment.update({'status': 'refunded', 'transaction_amount_refunded': payment['transaction_amount']})
        return dict(order)

    def search_payments(self, begin_utc, end_utc, offset=0):
        self._maybe_fail('search')
        results = self.payments[offset:offset + 50]
        return {'results': [dict(p) for p in results], 'paging': {'total': len(self.payments), 'offset': offset}}
