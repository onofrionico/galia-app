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


# La importación de la historia puede tardar horas: se la da por muerta si no late en 2 horas.
STALE_AFTER_BY_KIND = {'sales_history': timedelta(hours=2)}


def _last_sign_of_life(run):
    beat = (run.stats or {}).get('heartbeat') if isinstance(run.stats, dict) else None
    try:
        return max(run.started_at, datetime.fromisoformat(beat)) if beat else run.started_at
    except ValueError:
        return run.started_at


def expire_stale(kind, now=None):
    """Marca como abandonadas las corridas `running` sin señales de vida (su hilo murió). No commitea."""
    now = now or datetime.utcnow()
    limit = STALE_AFTER_BY_KIND.get(kind, STALE_AFTER)
    for running in FudoSyncRun.query.filter_by(kind=kind, status='running').all():
        if now - _last_sign_of_life(running) >= limit:
            running.status = 'error'
            running.finished_at = now
            running.error = f'Corrida abandonada (sin avances en {int(limit.total_seconds() // 60)} minutos)'


def heartbeat(run_id, now=None):
    """La corrida sigue viva (la importación de la historia late una vez por mes). Commitea."""
    run = db.session.get(FudoSyncRun, run_id)
    if run is None or run.status != 'running':
        return
    run.stats = {**(run.stats or {}), 'heartbeat': (now or datetime.utcnow()).isoformat()}
    db.session.commit()


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
