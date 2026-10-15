"""Cola de impresión del POS: comandas por estación, precuenta, ticket, reimpresión y estado.

Las funciones de creación (jobs_for_batch, jobs_for_void, add_job) no hacen commit: corren dentro de la
transacción de la venta. Las acciones de la cola hacen commit.
"""
from collections import OrderedDict
from datetime import timedelta

from sqlalchemy import and_, or_

from app.extensions import db
from app.models import ProductVariant
from app.models.pos import PrintJob, PrintPoint, PrintStation, Printer
from app.services.pos import print_documents as documents
from app.services.pos.common import load_sale, now, parse_id
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.validation import clean_str

CLAIM_LIMIT = 10
STALE_PRINTING = timedelta(seconds=60)
RETRY_AFTER = timedelta(seconds=15)
MAX_ATTEMPTS = 5
PROBLEM_AGE = timedelta(seconds=30)
POINT_DOWN = timedelta(seconds=30)


def station_printer(station_id):
    if station_id is None:
        return None
    return Printer.query.filter_by(station_id=station_id, is_active=True).order_by(Printer.id).first()


def cashier_printer():
    return Printer.query.filter_by(is_cashier=True, is_active=True).order_by(Printer.id).first()


def add_job(kind, printer, user, document, sale=None, station_id=None, batch=None, reprint_of=None):
    job = PrintJob(kind=kind, printer_id=printer.id, sale_id=sale.id if sale is not None else None,
                   station_id=station_id, batch=batch, document=document, status='pending', attempts=0,
                   created_by=user.id, created_at=now(), reprint_of=reprint_of)
    db.session.add(job)
    return job


def _station_of(item):
    variant = db.session.get(ProductVariant, item.product_variant_id)
    category = variant.product.category if variant is not None else None
    return category.station_id if category is not None else None


def _by_station(items):
    groups = OrderedDict()
    for item in items:
        station_id = _station_of(item)
        if station_id is not None:
            groups.setdefault(station_id, []).append(item)
    return groups


def _station_jobs(kind, sale, items, user, build):
    jobs = []
    for station_id, group in _by_station(items).items():
        station = db.session.get(PrintStation, station_id)
        printer = station_printer(station_id)
        if station is None or not station.is_active or printer is None:
            continue
        jobs.append(add_job(kind, printer, user, build(station, group), sale, station_id, group[0].batch))
    return jobs


def jobs_for_batch(sale, items, user):
    """Una comanda por estación con los ítems recién confirmados. Sin estación o sin impresora: nada."""
    return _station_jobs('order', sale, items, user,
                         lambda station, group: documents.order_document(sale, station, group[0].batch, group))


def jobs_for_void(sale, items, user, reason):
    """Una comanda de anulación por estación con los ítems confirmados que se anularon."""
    return _station_jobs('void', sale, items, user,
                         lambda station, group: documents.void_document(sale, station, group, reason))


def _require_cashier():
    printer = cashier_printer()
    if printer is None:
        raise PosError('No hay impresora de caja configurada')
    return printer


def print_bill(user, sale_id):
    sale = load_sale(sale_id)
    if sale.status not in ('open', 'billing') or not any(i.status == 'confirmed' for i in sale.items):
        raise PosError('La venta no tiene ítems confirmados para la precuenta')
    job = add_job('bill', _require_cashier(), user, documents.bill_document(sale), sale)
    db.session.commit()
    return job


def print_receipt(user, sale_id):
    sale = load_sale(sale_id)
    if sale.status != 'closed':
        raise PosError('Solo se imprime el ticket de una venta cerrada')
    job = add_job('receipt', _require_cashier(), user, documents.receipt_document(sale), sale)
    db.session.commit()
    return job


def _load_job(job_id, lock=True):
    query = PrintJob.query.filter_by(id=parse_id(job_id, 'El trabajo'))
    if lock:
        query = query.with_for_update().populate_existing()
    job = query.first()
    if job is None:
        raise not_found('El trabajo de impresión no existe')
    return job


def reprint(user, job_id):
    original = _load_job(job_id, lock=False)
    if original.kind in ('order', 'void'):
        printer = station_printer(original.station_id)
        if printer is None:
            raise PosError('La estación no tiene una impresora activa')
    elif original.kind == 'test':
        printer = original.printer
    else:
        printer = _require_cashier()
    job = add_job(original.kind, printer, user, documents.mark_reprint(original.document), original.sale,
                  original.station_id, original.batch, reprint_of=original.id)
    db.session.commit()
    return job


def test_print(user, printer_id):
    printer = db.session.get(Printer, parse_id(printer_id, 'La impresora'))
    if printer is None or not printer.is_active:
        raise not_found('La impresora no existe')
    job = add_job('test', printer, user, documents.test_document(printer))
    db.session.commit()
    return job


def _recover():
    """Devuelve a la cola lo que quedó imprimiendo sin respuesta y los fallidos que pueden reintentarse."""
    moment = now()
    PrintJob.query.filter(PrintJob.status == 'printing', PrintJob.claimed_at < moment - STALE_PRINTING).update(
        {'status': 'pending', 'claimed_by': None, 'claimed_at': None}, synchronize_session=False)
    PrintJob.query.filter(PrintJob.status == 'failed', PrintJob.attempts < MAX_ATTEMPTS,
                          PrintJob.failed_at < moment - RETRY_AFTER).update(
        {'status': 'pending', 'claimed_by': None, 'claimed_at': None}, synchronize_session=False)


def claim(print_point):
    point = clean_str(print_point, 60)
    if not point:
        raise bad_request('Indicá el punto de impresión')
    _recover()
    # El punto existe desde que se configuró una impresora: solo se actualiza (sin inserts concurrentes).
    PrintPoint.query.filter_by(name=point).update({'last_seen_at': now()}, synchronize_session=False)
    printer_ids = [p.id for p in Printer.query.filter_by(print_point=point, is_active=True)]
    jobs = []
    if printer_ids:
        query = (PrintJob.query.filter(PrintJob.printer_id.in_(printer_ids), PrintJob.status == 'pending')
                 .order_by(PrintJob.id).limit(CLAIM_LIMIT))
        if db.engine.dialect.name == 'postgresql':
            query = query.with_for_update(skip_locked=True)
        # populate_existing: los updates masivos de _recover no refrescan los objetos ya cargados.
        jobs = query.populate_existing().all()
        for job in jobs:
            job.status = 'printing'
            job.claimed_by = point
            job.claimed_at = now()
    db.session.commit()
    return jobs


def mark_done(job_id):
    job = _load_job(job_id)
    job.status = 'printed'
    job.printed_at = now()
    job.error = None
    db.session.commit()
    return job


def mark_failed(job_id, error):
    job = _load_job(job_id)
    if job.status == 'printed':
        db.session.commit()
        return job
    job.attempts += 1
    job.status = 'failed'
    job.error = (error if isinstance(error, str) else '').strip()[:255] or 'Error desconocido'
    job.failed_at = now()
    job.claimed_by = None
    job.claimed_at = None
    db.session.commit()
    return job


def retry(job_id):
    job = _load_job(job_id)
    if job.status == 'printed':
        raise PosError('El trabajo ya se imprimió')
    job.status = 'pending'
    job.attempts = 0
    job.error = None
    job.claimed_by = None
    job.claimed_at = None
    db.session.commit()
    return job


def mark_printed(job_id):
    job = _load_job(job_id)
    job.status = 'printed'
    job.printed_at = now()
    job.claimed_by = 'manual'
    db.session.commit()
    return job


def _place(job):
    sale = job.sale
    if sale is None:
        return None
    return sale.table.label if sale.table is not None else f'Mostrador #{sale.number}'


def job_to_dict(job, with_printer=False):
    printer = {'id': job.printer.id, 'name': job.printer.name}
    if with_printer:
        printer.update({'connection': job.printer.connection, 'host': job.printer.host, 'port': job.printer.port,
                        'os_name': job.printer.os_name, 'paper_width': job.printer.paper_width})
    return {
        'id': job.id, 'kind': job.kind, 'status': job.status, 'printer': printer, 'sale_id': job.sale_id,
        'sale_number': job.sale.number if job.sale else None, 'place': _place(job),
        'station_name': job.station.name if job.station else None, 'batch': job.batch, 'attempts': job.attempts,
        'error': job.error, 'created_at': job.created_at.isoformat(),
        'printed_at': job.printed_at.isoformat() if job.printed_at else None, 'reprint_of': job.reprint_of,
        'document': job.document,
    }


def _active_points():
    names = sorted({p.print_point for p in Printer.query.filter_by(is_active=True)})
    return [db.session.get(PrintPoint, name) or PrintPoint(name=name) for name in names]


def status():
    moment = now()
    problems = (PrintJob.query.filter(or_(PrintJob.status == 'failed',
                                          and_(PrintJob.status.in_(('pending', 'printing')),
                                               PrintJob.created_at < moment - PROBLEM_AGE)))
                .order_by(PrintJob.id).limit(50).all())
    points = [{'name': p.name, 'last_seen_at': p.last_seen_at.isoformat() if p.last_seen_at else None,
               'down': p.last_seen_at is None or p.last_seen_at < moment - POINT_DOWN} for p in _active_points()]
    pending = PrintJob.query.filter(PrintJob.status.in_(('pending', 'printing'))).count()
    return {'problems': [job_to_dict(j) for j in problems], 'points': points, 'pending': pending}


def sale_jobs(sale_id):
    return PrintJob.query.filter_by(sale_id=parse_id(sale_id, 'La venta')).order_by(PrintJob.id).all()


def print_points():
    printers = Printer.query.filter_by(is_active=True).order_by(Printer.print_point, Printer.name).all()
    grouped = OrderedDict()
    for printer in printers:
        grouped.setdefault(printer.print_point, []).append(printer.to_dict())
    return [{'name': name, 'printers': items} for name, items in grouped.items()]
