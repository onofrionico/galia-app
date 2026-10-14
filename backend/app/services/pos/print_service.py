"""Cola de impresión del POS: comandas por estación, precuenta, ticket, reimpresión y estado.

Las funciones de creación (jobs_for_batch, jobs_for_void, add_job) no hacen commit: corren dentro de la
transacción de la venta. Las acciones de la cola hacen commit.
"""
from collections import OrderedDict

from app.extensions import db
from app.models import ProductVariant
from app.models.pos import PrintJob, PrintStation, Printer
from app.services.pos import print_documents as documents
from app.services.pos.common import now


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
