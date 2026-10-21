"""Comprobantes ARCA: vista previa, emisión en dos fases, resolución de pendientes, nota de crédito, listado.

Fase 1 (transacción con la fila de fiscal_settings bloqueada): valida, resuelve pendientes viejos, toma el
próximo número de ARCA y guarda el comprobante 'pending'. Fase 2 (sin transacción abierta): pide el CAE.
Si la respuesta no llega, el comprobante queda 'pending' y se resuelve consultando a ARCA (nunca a ciegas).
"""
import logging
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

from app.extensions import db
from app.models import FiscalCustomer, Invoice, InvoicePayment, PaymentMethod
from app.models.fiscal import VOUCHER_TYPES
from app.models.pos import PosSale
from app.services.fiscal import amounts, arca, receivers
from app.services.fiscal import settings as fiscal_settings
from app.services.fiscal.arca import ArcaRejected, ArcaUnavailable, wsfe
from app.services.fiscal.invoice_documents import invoice_document
from app.services.pos import print_documents, print_service
from app.services.pos.common import load_sale, now, parse_id, require_module
from app.services.pos.errors import PosError, not_found
from app.utils.timezone_utils import get_current_date_argentina

logger = logging.getLogger(__name__)
PENDING_GRACE = timedelta(seconds=120)
UNAVAILABLE = 'ARCA no responde, probá en unos minutos'
NOT_CONFIRMED = 'No pudimos confirmar con ARCA. Tocá Verificar en unos segundos'
STILL_PROCESSING = 'Todavía no aparece en ARCA: probá Verificar de nuevo en un minuto'
PRINT_FAILED = 'La factura se emitió, pero no se pudo mandar a imprimir: reimprimila'


def _external_ids():
    return {m.id for m in PaymentMethod.query.filter_by(invoiced_externally=True)}


def _authorized_credit_note(invoice):
    return Invoice.query.filter_by(related_invoice_id=invoice.id, status='authorized').first()


def active_invoice(sale_id):
    """Factura autorizada de la venta sin nota de crédito autorizada (como máximo una)."""
    for invoice in Invoice.query.filter_by(sale_id=sale_id, kind='invoice', status='authorized') \
            .order_by(Invoice.id.desc()):
        if _authorized_credit_note(invoice) is None:
            return invoice
    return None


def pending_invoice(sale_id):
    return Invoice.query.filter_by(sale_id=sale_id, status='pending').order_by(Invoice.id.desc()).first()


def preview(sale_id):
    sale = load_sale(parse_id(sale_id, 'La venta'))
    settings = fiscal_settings.get_settings()
    amount = amounts.invoiceable_amount(sale, _external_ids())
    mode, lines = amounts.build_lines(sale, amount, print_documents.item_description) if amount else (None, [])
    condition = settings.iva_condition if settings else 'monotributo'
    voucher_type = receivers.voucher_type_for(condition, 'consumidor_final')
    active = active_invoice(sale.id)
    pending = pending_invoice(sale.id)
    missing = fiscal_settings.missing(settings)
    data = {
        'sale_id': sale.id, 'sale_status': sale.status, 'total': f'{sale.total:.2f}', 'amount': f'{amount:.2f}',
        'detail_mode': mode, 'lines': lines, 'voucher_type': voucher_type,
        'letter': VOUCHER_TYPES[voucher_type][1],
        'requires_id_from': (f'{settings.cf_id_threshold:.2f}'
                             if settings and settings.cf_id_threshold is not None else None),
        'ready': not missing, 'missing': missing,
        'environment': settings.environment if settings else 'homologacion',
        'active_invoice': invoice_to_dict(active) if active else None,
        'pending_invoice': invoice_to_dict(pending) if pending else None,
    }
    db.session.commit()  # libera el lock de la venta
    return data


def _save_customer(receiver):
    if receiver['doc_type'] is None:
        return None
    customer = FiscalCustomer.query.filter_by(doc_type=receiver['doc_type'],
                                              doc_number=receiver['doc_number']).first()
    if customer is None:
        customer = FiscalCustomer(doc_type=receiver['doc_type'], doc_number=receiver['doc_number'],
                                  created_at=now())
        db.session.add(customer)
    customer.name = receiver['name']
    customer.iva_condition = receiver['iva_condition']
    customer.address = receiver['address']
    customer.updated_at = now()
    db.session.flush()
    return customer


def _discriminates_iva(voucher_type):
    """A y B discriminan IVA; C no. Depende del comprobante, no de la configuración actual."""
    return VOUCHER_TYPES[voucher_type][1] != 'C'


def _detail_fields(invoice, settings, associated=None):
    return {'number': invoice.number, 'voucher_date': invoice.voucher_date,
            'doc_type_code': invoice.receiver_doc_type, 'doc_number': invoice.receiver_doc_number,
            'total': invoice.total, 'net': invoice.net, 'iva': invoice.iva, 'iva_rate': invoice.iva_rate,
            'discriminated': _discriminates_iva(invoice.voucher_type),
            'receiver_iva_id': receivers.RECEIVER_IVA_IDS[invoice.receiver_iva_condition], 'associated': associated}


def resolve(invoice, gateway):
    """Decide un 'pending' preguntándole a ARCA si ese número quedó autorizado. No hace commit.

    Si ARCA todavía no lo tiene y el pedido es reciente, sigue 'pending': ARCA puede estar procesándolo
    aunque nuestro pedido haya dado timeout. Recién pasado PENDING_GRACE se da por no recibido."""
    found = gateway.query(invoice.voucher_type, invoice.point_of_sale, invoice.number)
    if found is None:
        if invoice.created_at > now() - PENDING_GRACE:
            invoice.error = STILL_PROCESSING
            return invoice
        invoice.status = 'rejected'
        invoice.error = 'No llegó a ARCA'
        return invoice
    request = invoice.request or {}
    if found['total'] != Decimal(invoice.total).quantize(Decimal('0.01')) or \
            int(found['doc_number'] or 0) != int(request.get('DocNro') or 0):
        logger.error('ARCA tiene otro comprobante en %s: %s', invoice.label, found)
        invoice.status = 'rejected'
        invoice.error = 'ARCA tiene otro comprobante con ese número'
        invoice.arca_result = {'query': {k: str(v) for k, v in found.items()}}
        return invoice
    invoice.status = 'authorized'
    invoice.cae = found['cae']
    invoice.cae_due = found['cae_due']
    invoice.authorized_at = now()
    invoice.error = None
    return invoice


def print_invoice(invoice, user, settings=None):
    """Encola la impresión en la impresora de caja. Sin impresora, deja el aviso en `invoice.print_warning`
    (atributo de la instancia, no columna: solo vive en este pedido) y lo devuelve. No hace commit.
    `user` None (pendiente resuelto durante otra emisión): el trabajo queda a nombre de quien emitió."""
    settings = settings or fiscal_settings.get_settings()
    printer = print_service.cashier_printer()
    if printer is None:
        invoice.print_warning = 'No hay impresora de caja configurada'
        return invoice.print_warning
    author = user or SimpleNamespace(id=invoice.created_by)  # add_job solo usa user.id
    try:
        document = invoice_document(invoice, settings)
        print_service.add_job('invoice', printer, author, document, invoice.sale)
    except Exception:  # la impresión nunca deshace una factura autorizada
        logger.exception('No se pudo encolar la impresión de %s', invoice.label)
        invoice.print_warning = PRINT_FAILED
        return invoice.print_warning
    invoice.print_warning = None
    return None


def _resolve_stale(settings, voucher_type, gateway):
    pending = Invoice.query.filter_by(environment=settings.environment, point_of_sale=settings.point_of_sale,
                                      voucher_type=voucher_type, status='pending').all()
    for invoice in pending:
        if invoice.created_at > now() - PENDING_GRACE:
            raise PosError('Hay una factura emitiéndose, probá en unos segundos')
        resolve(invoice, gateway)
        if invoice.status == 'authorized':
            print_invoice(invoice, None, settings)


def _reserve(user, settings, gateway, sale, kind, voucher_type, receiver, mode, lines, total, payments,
             related=None, customer=None):
    """Fase 1: número de ARCA + comprobante 'pending' con el pedido completo. Hace commit.

    Una nota de crédito copia neto, IVA y alícuota de la factura que anula."""
    _resolve_stale(settings, voucher_type, gateway)
    number = gateway.last_authorized(settings.point_of_sale, voucher_type) + 1
    if related is not None:
        net, iva, rate = related.net, related.iva, related.iva_rate
    else:
        discriminated = _discriminates_iva(voucher_type)
        rate = Decimal(settings.default_iva_rate) if discriminated else Decimal('0')
        net, iva = amounts.split_iva(total, rate, discriminated)
    invoice = Invoice(kind=kind, voucher_type=voucher_type, environment=settings.environment,
                      point_of_sale=settings.point_of_sale, number=number, sale_id=sale.id if sale else None,
                      related_invoice_id=related.id if related else None,
                      customer_id=customer.id if customer else None,
                      receiver_doc_type=receiver['doc_type_code'], receiver_doc_number=receiver['doc_number'],
                      receiver_name=receiver['name'], receiver_iva_condition=receiver['iva_condition'],
                      receiver_address=receiver['address'], detail_mode=mode, lines=lines, total=total, net=net,
                      iva=iva, iva_rate=rate, voucher_date=get_current_date_argentina(), status='pending',
                      request={}, created_by=user.id, created_at=now())
    associated = None
    if related is not None:
        associated = {'type': related.voucher_type, 'pos': related.point_of_sale, 'number': related.number,
                      'cuit': settings.cuit, 'date': related.voucher_date}
    invoice.request = wsfe.build_detail(_detail_fields(invoice, settings, associated))
    db.session.add(invoice)
    for payment_id, amount in payments:
        invoice.payments.append(InvoicePayment(payment_id=payment_id, amount=amount))
    db.session.commit()
    return invoice


def _request_cae(invoice, settings, gateway, user):
    """Fase 2: pedido de CAE. Siempre deja el comprobante guardado (commit)."""
    try:
        result = gateway.request_cae(invoice.point_of_sale, invoice.voucher_type, invoice.request)
    except ArcaUnavailable as exc:
        logger.warning('ARCA sin respuesta para %s: %s', invoice.label, exc)
        invoice.error = NOT_CONFIRMED
        db.session.commit()
        return invoice
    except ArcaRejected as exc:
        logger.warning('ARCA devolvió errores para %s: %s', invoice.label, exc)
        invoice.status = 'rejected'
        invoice.arca_result = {'errors': exc.errors}
        invoice.error = f'ARCA rechazó la factura: {exc.errors[0]["msg"]}' if exc.errors else UNAVAILABLE
        db.session.commit()
        return invoice
    invoice.arca_result = {'observations': result.observations, 'errors': result.errors}
    if result.result == 'A':
        invoice.status = 'authorized'
        invoice.cae = result.cae
        invoice.cae_due = result.cae_due
        invoice.authorized_at = now()
        invoice.error = None
        db.session.commit()  # la autorización queda guardada antes de imprimir
        print_invoice(invoice, user, settings)
    else:
        invoice.status = 'rejected'
        messages = [o['msg'] for o in result.observations] or [e['msg'] for e in result.errors]
        invoice.error = f'ARCA rechazó la factura: {"; ".join(messages) or "sin detalle"}'
    db.session.commit()
    return invoice


def _gateway_or_error(settings):
    try:
        return arca.get_gateway(settings)
    except ArcaUnavailable as exc:
        logger.warning('WSAA sin respuesta: %s', exc)
        raise PosError(UNAVAILABLE)
    except ArcaRejected as exc:
        raise PosError(f'ARCA rechazó el acceso: {exc.errors[0]["msg"]}')


def issue(user, sale_id, customer_data):
    target = db.session.get(PosSale, parse_id(sale_id, 'La venta'))
    if target is not None and target.is_practice:
        raise PosError('En modo práctica no se factura')
    settings = fiscal_settings.get_settings()
    fiscal_settings.require_ready(settings)
    gateway = _gateway_or_error(settings)  # WSAA antes del lock: el token se guarda con su propio commit
    try:
        settings = fiscal_settings.get_settings(lock=True)
        sale = load_sale(parse_id(sale_id, 'La venta'))
        if sale.status != 'closed':
            raise PosError('Solo se factura una venta cerrada')
        active = active_invoice(sale.id)
        if active is not None:
            raise PosError(f'La venta ya tiene la {active.label}')
        if pending_invoice(sale.id) is not None:
            raise PosError('Hay una factura sin confirmar en esta venta: verificala antes')
        external = _external_ids()
        payments = amounts.invoiceable_payments(sale, external)
        total = amounts.invoiceable_amount(sale, external)
        if not total:
            raise PosError('Todo lo cobrado en esta venta lo factura otro sistema')
        receiver = receivers.normalize_receiver(customer_data, total, settings.cf_id_threshold,
                                                settings.iva_condition)
        voucher_type = receivers.voucher_type_for(settings.iva_condition, receiver['iva_condition'])
        mode, lines = amounts.build_lines(sale, total, print_documents.item_description)
        customer = _save_customer(receiver)
        invoice = _reserve(user, settings, gateway, sale, 'invoice', voucher_type, receiver, mode, lines, total,
                           [(p.id, p.amount) for p in payments], customer=customer)
    except ArcaUnavailable as exc:
        db.session.rollback()
        logger.warning('ARCA sin respuesta al reservar: %s', exc)
        raise PosError(UNAVAILABLE)
    except ArcaRejected as exc:
        db.session.rollback()
        raise PosError(f'ARCA rechazó el pedido: {exc.errors[0]["msg"]}')
    return _request_cae(invoice, settings, gateway, user)


def cancel(user, invoice_id):
    """'Anular factura': nota de crédito por el total de una factura vigente."""
    require_module(user, 'Anular', 'No tenés permiso para anular facturas')
    settings = fiscal_settings.get_settings()
    fiscal_settings.require_ready(settings)
    gateway = _gateway_or_error(settings)
    try:
        settings = fiscal_settings.get_settings(lock=True)
        invoice = _load_invoice(invoice_id)
        if invoice.kind != 'invoice' or invoice.status != 'authorized' or _authorized_credit_note(invoice):
            raise PosError('Solo se anula una factura vigente')
        if Invoice.query.filter_by(related_invoice_id=invoice.id, status='pending').first():
            raise PosError('Hay una nota de crédito sin confirmar para esta factura: verificala antes')
        if invoice.environment != settings.environment:
            raise PosError('La factura es de otro entorno: cambiá el entorno en Ajustes → Facturación')
        voucher_type = receivers.credit_note_type_for(invoice.voucher_type)
        receiver = {'doc_type_code': invoice.receiver_doc_type, 'doc_number': invoice.receiver_doc_number,
                    'name': invoice.receiver_name, 'iva_condition': invoice.receiver_iva_condition,
                    'address': invoice.receiver_address}
        customer = db.session.get(FiscalCustomer, invoice.customer_id) if invoice.customer_id else None
        credit = _reserve(user, settings, gateway, invoice.sale, 'credit_note', voucher_type, receiver,
                          invoice.detail_mode, invoice.lines, Decimal(invoice.total),
                          [(p.payment_id, p.amount) for p in invoice.payments], related=invoice,
                          customer=customer)
    except ArcaUnavailable as exc:
        db.session.rollback()
        logger.warning('ARCA sin respuesta al reservar la nota de crédito: %s', exc)
        raise PosError(UNAVAILABLE)
    except ArcaRejected as exc:
        db.session.rollback()
        raise PosError(f'ARCA rechazó el pedido: {exc.errors[0]["msg"]}')
    return _request_cae(credit, settings, gateway, user)


def _load_invoice(invoice_id):
    invoice = db.session.get(Invoice, parse_id(invoice_id, 'El comprobante'))
    if invoice is None:
        raise not_found('El comprobante no existe')
    return invoice


def verify(user, invoice_id):
    invoice = _load_invoice(invoice_id)
    if invoice.status != 'pending':
        return invoice
    settings = fiscal_settings.get_settings()
    if invoice.environment != settings.environment:
        # Consultar en otro entorno daría "no existe" y rechazaría un comprobante que sí está autorizado.
        raise PosError('El comprobante es de otro entorno: cambiá el entorno en Ajustes → Facturación')
    gateway = _gateway_or_error(settings)
    try:
        resolve(invoice, gateway)
    except (ArcaUnavailable, ArcaRejected) as exc:
        db.session.rollback()
        logger.warning('No se pudo verificar %s: %s', invoice.label, exc)
        raise PosError(UNAVAILABLE)
    db.session.commit()  # la autorización queda guardada antes de imprimir
    if invoice.status == 'authorized':
        print_invoice(invoice, user, settings)
        db.session.commit()
    return invoice


def reprint(user, invoice_id):
    invoice = _load_invoice(invoice_id)
    if invoice.status != 'authorized':
        raise PosError('Solo se reimprime un comprobante autorizado')
    warning = print_invoice(invoice, user)
    if warning:
        raise PosError(warning)
    db.session.commit()
    return invoice


def _sale_link(sale):
    """Ruta del POS que abre la venta (salón o mostrador), para el listado de comprobantes."""
    if sale is None:
        return None
    if sale.table is not None:
        return f'/pos/salon/{sale.table.salon_id}?sale={sale.id}'
    return f'/pos/mostrador?sale={sale.id}'


def invoice_to_dict(invoice):
    credit_note = _authorized_credit_note(invoice) if invoice.kind == 'invoice' else None
    return {
        'sale_link': _sale_link(invoice.sale),
        'id': invoice.id, 'kind': invoice.kind, 'voucher_type': invoice.voucher_type, 'letter': invoice.letter,
        'label': invoice.label, 'environment': invoice.environment, 'point_of_sale': invoice.point_of_sale,
        'number': invoice.number, 'sale_id': invoice.sale_id,
        'sale_number': invoice.sale.number if invoice.sale else None,
        'related_invoice_id': invoice.related_invoice_id,
        'related_label': invoice.related.label if invoice.related else None,
        'receiver': {'doc_type': invoice.receiver_doc_type, 'doc_number': invoice.receiver_doc_number,
                     'name': invoice.receiver_name, 'iva_condition': invoice.receiver_iva_condition,
                     'address': invoice.receiver_address},
        'detail_mode': invoice.detail_mode, 'lines': invoice.lines, 'total': f'{invoice.total:.2f}',
        'net': f'{invoice.net:.2f}', 'iva': f'{invoice.iva:.2f}', 'voucher_date': invoice.voucher_date.isoformat(),
        'status': invoice.status, 'cae': invoice.cae,
        'cae_due': invoice.cae_due.isoformat() if invoice.cae_due else None, 'error': invoice.error,
        'arca_result': invoice.arca_result, 'request': invoice.request,
        'created_at': invoice.created_at.isoformat(),
        'authorized_at': invoice.authorized_at.isoformat() if invoice.authorized_at else None,
        'is_active': invoice.kind == 'invoice' and invoice.status == 'authorized' and credit_note is None,
        'credit_note_label': credit_note.label if credit_note else None,
        'print_warning': getattr(invoice, 'print_warning', None),
    }


LIST_PAGE_SIZE = 50


def list_invoices(date_from=None, date_to=None, kind=None, status=None, page=1):
    """Comprobantes del entorno activo, más nuevos primero. Fechas por día de comprobante (Argentina)."""
    settings = fiscal_settings.get_settings()
    environment = settings.environment if settings else 'homologacion'
    query = Invoice.query.filter_by(environment=environment)
    if date_from:
        query = query.filter(Invoice.voucher_date >= date_from)
    if date_to:
        query = query.filter(Invoice.voucher_date <= date_to)
    if kind in ('invoice', 'credit_note'):
        query = query.filter_by(kind=kind)
    if status in ('pending', 'authorized', 'rejected'):
        query = query.filter_by(status=status)
    total = query.count()
    rows = query.order_by(Invoice.id.desc()).offset((page - 1) * LIST_PAGE_SIZE).limit(LIST_PAGE_SIZE).all()
    return {'invoices': [invoice_to_dict(i) for i in rows], 'page': page,
            'pages': max(1, -(-total // LIST_PAGE_SIZE)), 'total': total, 'environment': environment}


def sale_invoices(sale_id):
    rows = Invoice.query.filter_by(sale_id=parse_id(sale_id, 'La venta')).order_by(Invoice.id).all()
    return [invoice_to_dict(i) for i in rows]


def get_invoice(invoice_id):
    return invoice_to_dict(_load_invoice(invoice_id))


def search_customers(q):
    """Hasta 10 clientes: por número de documento si se escribieron solo números, si no por nombre."""
    text = (q or '').strip()
    if len(text) < 2:
        return []
    digits = ''.join(ch for ch in text if ch.isdigit())
    query = FiscalCustomer.query
    if digits and len(digits) == len(text.replace('-', '').replace('.', '')):
        query = query.filter(FiscalCustomer.doc_number.startswith(digits))
    else:
        query = query.filter(FiscalCustomer.name.ilike(f'%{text}%'))
    return [c.to_dict() for c in query.order_by(FiscalCustomer.name).limit(10)]


def test_connection():
    """Para Ajustes → Facturación: estado del servicio y último comprobante del punto de venta."""
    settings = fiscal_settings.get_settings()
    fiscal_settings.require_ready(settings)
    gateway = _gateway_or_error(settings)
    voucher_type = receivers.voucher_type_for(settings.iva_condition, 'consumidor_final')
    try:
        gateway.dummy()
        last = gateway.last_authorized(settings.point_of_sale, voucher_type)
    except ArcaUnavailable:
        raise PosError(UNAVAILABLE)
    except ArcaRejected as exc:
        raise PosError(f'ARCA respondió: {exc.errors[0]["msg"]}')
    letter = VOUCHER_TYPES[voucher_type][1]
    return {'ok': True, 'last_number': last,
            'label': f'Último comprobante: {letter} {settings.point_of_sale:05d}-{last:08d}'}
