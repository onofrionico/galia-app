"""WSFEv1: último comprobante, pedido de CAE y consulta. El armado y la lectura son funciones puras."""
from collections import namedtuple
from datetime import datetime
from decimal import Decimal

from app.services.fiscal.arca import ArcaRejected, ArcaUnavailable

URLS = {'homologacion': 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL',
        'produccion': 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'}
IVA_IDS = {Decimal('0'): 3, Decimal('10.5'): 4, Decimal('21'): 5, Decimal('27'): 6}
NOT_FOUND_CODE = 602

CaeResult = namedtuple('CaeResult', 'result cae cae_due observations errors')


def _date(value):
    return value.strftime('%Y%m%d')


def _parse_date(value):
    return datetime.strptime(str(value), '%Y%m%d').date() if value else None


def _amount(value):
    return float(Decimal(value).quantize(Decimal('0.01')))


def _messages(container, key):
    items = container.get(key) if isinstance(container, dict) else None
    return [{'code': item.get('Code'), 'msg': item.get('Msg')} for item in (items or [])]


def build_detail(fields):
    """FECAEDetRequest de un comprobante. `fields`: number, voucher_date, doc_type_code, doc_number, total,
    net, iva, iva_rate, discriminated, receiver_iva_id, associated (dict o None)."""
    detail = {
        'Concepto': 1, 'DocTipo': fields['doc_type_code'], 'DocNro': int(fields['doc_number'] or 0),
        'CbteDesde': fields['number'], 'CbteHasta': fields['number'], 'CbteFch': _date(fields['voucher_date']),
        'ImpTotal': _amount(fields['total']), 'ImpTotConc': 0, 'ImpNeto': _amount(fields['net']), 'ImpOpEx': 0,
        'ImpIVA': _amount(fields['iva']), 'ImpTrib': 0, 'MonId': 'PES', 'MonCotiz': 1,
        'CondicionIVAReceptorId': fields['receiver_iva_id'],
    }
    if fields['discriminated']:
        detail['Iva'] = {'AlicIva': [{'Id': IVA_IDS[Decimal(fields['iva_rate'])],
                                      'BaseImp': _amount(fields['net']), 'Importe': _amount(fields['iva'])}]}
    associated = fields.get('associated')
    if associated:
        detail['CbtesAsoc'] = {'CbteAsoc': [{'Tipo': associated['type'], 'PtoVta': associated['pos'],
                                             'Nro': associated['number'], 'Cuit': associated['cuit'],
                                             'CbteFch': _date(associated['date'])}]}
    return detail


def parse_cae_response(data):
    errors = _messages(data.get('Errors'), 'Err')
    details = (data.get('FeDetResp') or {}).get('FECAEDetResponse') or []
    if not details:
        raise ArcaRejected(errors or [{'code': 'wsfe', 'msg': 'Respuesta de ARCA sin detalle'}])
    detail = details[0]
    observations = _messages(detail.get('Observaciones'), 'Obs')
    return CaeResult(detail.get('Resultado'), detail.get('CAE') or None, _parse_date(detail.get('CAEFchVto')),
                     observations, errors)


def parse_query_response(data):
    errors = _messages(data.get('Errors'), 'Err')
    if any(e['code'] == NOT_FOUND_CODE for e in errors):
        return None
    if errors:
        raise ArcaRejected(errors)
    result = data.get('ResultGet') or {}
    if not result.get('CodAutorizacion'):
        return None
    return {'cae': str(result['CodAutorizacion']), 'cae_due': _parse_date(result.get('FchVto')),
            'total': Decimal(str(result.get('ImpTotal'))).quantize(Decimal('0.01')),
            'doc_type': int(result.get('DocTipo')), 'doc_number': str(result.get('DocNro'))}


class WsfeClient:
    def __init__(self, environment, cuit, token, sign):
        self.environment = environment
        self.auth = {'Token': token, 'Sign': sign, 'Cuit': int(cuit)}
        self._client = None

    def _service(self):
        from zeep import Client
        from zeep.transports import Transport
        if self._client is None:
            self._client = Client(URLS[self.environment], transport=Transport(timeout=10, operation_timeout=30))
        return self._client.service

    def _call(self, name, **kwargs):
        from zeep.helpers import serialize_object
        try:
            response = getattr(self._service(), name)(**kwargs)
        except Exception as exc:  # red, timeout, SOAP Fault
            raise ArcaUnavailable(str(exc))
        return serialize_object(response, dict) or {}

    def dummy(self):
        return self._call('FEDummy')

    def last_authorized(self, pos, voucher_type):
        data = self._call('FECompUltimoAutorizado', Auth=self.auth, PtoVta=pos, CbteTipo=voucher_type)
        errors = _messages(data.get('Errors'), 'Err')
        if errors:
            raise ArcaRejected(errors)
        return int(data.get('CbteNro') or 0)

    def request_cae(self, pos, voucher_type, detail):
        data = self._call('FECAESolicitar', Auth=self.auth, FeCAEReq={
            'FeCabReq': {'CantReg': 1, 'PtoVta': pos, 'CbteTipo': voucher_type},
            'FeDetReq': {'FECAEDetRequest': [detail]}})
        return parse_cae_response(data)

    def query(self, voucher_type, pos, number):
        data = self._call('FECompConsultar', Auth=self.auth,
                          FeCompConsReq={'CbteTipo': voucher_type, 'CbteNro': number, 'PtoVta': pos})
        return parse_query_response(data)
