"""Registro de corridas de sincronización con Fudo y ejecución en segundo plano."""
import logging
from datetime import datetime, timedelta

from app.extensions import db
from app.models.fudo_sync_run import FudoSyncRun
from app.services import expense_sync_service

logger = logging.getLogger(__name__)

STALE_AFTER = timedelta(minutes=30)


class SyncInProgress(Exception):
    def __init__(self, run):
        super().__init__(f'Corrida {run.id} en curso')
        self.run = run


def expire_stale(kind, now=None):
    """Marca como abandonadas las corridas `running` de más de 30 min (su hilo murió). No commitea."""
    now = now or datetime.utcnow()
    for running in FudoSyncRun.query.filter_by(kind=kind, status='running').all():
        if now - running.started_at >= STALE_AFTER:
            running.status = 'error'
            running.finished_at = now
            running.error = 'Corrida abandonada (no terminó en 30 minutos)'


def start_run(kind, params, user_id=None, now=None):
    now = now or datetime.utcnow()
    expire_stale(kind, now)
    running = FudoSyncRun.query.filter_by(kind=kind, status='running').first()
    if running:
        raise SyncInProgress(running)
    run = FudoSyncRun(kind=kind, status='running', started_at=now, params=params, triggered_by=user_id)
    db.session.add(run)
    db.session.commit()
    return run


def finish_run(run_id, stats=None, error=None):
    run = db.session.get(FudoSyncRun, run_id)
    run.status = 'error' if error else 'ok'
    run.finished_at = datetime.utcnow()
    run.stats = stats
    run.error = error
    db.session.commit()


def run_sales_history(app, run_id, from_month, force, client_factory):
    """Importación de la historia de ventas de Fudo en segundo plano (kind='sales_history')."""
    from app.services import fudo_sales_import

    with app.app_context():
        try:
            stats = fudo_sales_import.import_history(client_factory(), from_month=from_month, force=force,
                                                     run_id=run_id)
        except Exception as exc:
            logger.exception('Importación de la historia de ventas %s falló', run_id)
            db.session.rollback()
            finish_run(run_id, error=str(exc) or exc.__class__.__name__)
            return
        finish_run(run_id, stats={'months': len(stats['months']), 'errors': stats['errors'],
                                  'changed_months': stats['changed_months']})


def run_expenses_sync(app, run_id, start_date, end_date, client_factory):
    with app.app_context():
        try:
            stats = expense_sync_service.sync_expenses(client_factory(), start_date, end_date)
        except Exception as exc:
            logger.exception('Sync de gastos %s falló', run_id)
            db.session.rollback()
            finish_run(run_id, error=str(exc) or exc.__class__.__name__)
            return
        finish_run(run_id, stats=stats)
