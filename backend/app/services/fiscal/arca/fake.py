"""ARCA de mentira para tests y para el preview local (FISCAL_FAKE_ARCA=1 con SQLite). Nunca en producción."""
import threading
from datetime import date, timedelta
from decimal import Decimal

from app.services.fiscal.arca import ArcaUnavailable
from app.services.fiscal.arca.wsfe import CaeResult


class FakeArca:
    issued = {}  # (pos, type) -> {number: {'cae', 'cae_due', 'total', 'doc_type', 'doc_number'}}
    mode = 'approve'  # approve | reject | timeout | timeout_after_issue
    _lock = threading.Lock()

    @classmethod
    def reset(cls, mode='approve'):
        with cls._lock:
            cls.issued = {}
            cls.mode = mode

    def dummy(self):
        return {'AppServer': 'OK', 'DbServer': 'OK', 'AuthServer': 'OK'}

    def last_authorized(self, pos, voucher_type):
        with self._lock:
            return max(self.issued.get((pos, voucher_type), {}) or [0])

    def request_cae(self, pos, voucher_type, detail):
        mode = type(self).mode
        if mode == 'timeout':
            raise ArcaUnavailable('timeout (simulado)')
        if mode == 'reject':
            return CaeResult('R', None, None, [{'code': 10015, 'msg': 'Documento del receptor inválido'}], [])
        number = detail['CbteDesde']
        with self._lock:
            book = type(self).issued.setdefault((pos, voucher_type), {})
            if number != max(book or [0]) + 1:
                return CaeResult('R', None, None, [{'code': 10016, 'msg': 'Número no correlativo'}], [])
            cae = f'7{pos:04d}{voucher_type:02d}{number:07d}'
            book[number] = {'cae': cae, 'cae_due': date.today() + timedelta(days=10),
                            'total': Decimal(str(detail['ImpTotal'])).quantize(Decimal('0.01')),
                            'doc_type': detail['DocTipo'], 'doc_number': str(detail['DocNro'])}
        if mode == 'timeout_after_issue':
            raise ArcaUnavailable('timeout después de autorizar (simulado)')
        return CaeResult('A', cae, book[number]['cae_due'], [], [])

    def query(self, voucher_type, pos, number):
        with self._lock:
            found = self.issued.get((pos, voucher_type), {}).get(number)
            return dict(found) if found else None
