from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models.expense import Expense
from app.models.fudo_sync_run import FudoSyncRun
from app.routes import fudo_sync
from app.services import fudo_sync_runs
from app.services.fudo_sync_runs import SyncInProgress
from fudo_expense_fakes import FakeExpensesClient, fudo_expense

URL = '/api/v1/fudo/sync/expenses'


@pytest.fixture
def run_inline(monkeypatch):
    """Corre la sync en el mismo hilo y con un cliente fake configurable."""
    holder = {'client': FakeExpensesClient(data=[fudo_expense(101)])}
    monkeypatch.setattr(fudo_sync, '_launch', lambda target, *args: target(*args))
    monkeypatch.setattr(fudo_sync, 'FudoClient', lambda: holder['client'])
    return holder


def test_start_run_blocks_recent_running(menu_app):
    now = datetime(2026, 10, 15, 12, 0)
    first = fudo_sync_runs.start_run('expenses', {}, now=now)

    with pytest.raises(SyncInProgress) as exc:
        fudo_sync_runs.start_run('expenses', {}, now=now + timedelta(minutes=10))
    assert exc.value.run.id == first.id


def test_start_run_abandons_stale_running(menu_app):
    now = datetime(2026, 10, 15, 12, 0)
    stale = fudo_sync_runs.start_run('expenses', {}, now=now)

    fresh = fudo_sync_runs.start_run('expenses', {}, now=now + timedelta(minutes=31))

    db.session.refresh(stale)
    assert stale.status == 'error'
    assert 'abandonada' in stale.error
    assert fresh.status == 'running'


def test_run_expenses_sync_records_error(menu_app):
    run = fudo_sync_runs.start_run('expenses', {})

    fudo_sync_runs.run_expenses_sync(menu_app, run.id, '2026-10-01', '2026-10-31',
                                     lambda: FakeExpensesClient(error=RuntimeError('401 Unauthorized')))

    db.session.expire_all()  # la corrida se cerró en la sesión del contexto interno
    run = db.session.get(FudoSyncRun, run.id)
    assert run.status == 'error'
    assert run.error == '401 Unauthorized'
    assert run.finished_at is not None


def test_post_runs_sync_and_records_stats(menu_client, admin_headers, run_inline):
    response = menu_client.post(f'{URL}?start_date=2026-10-01&end_date=2026-10-31', headers=admin_headers)

    assert response.status_code == 202
    run_id = response.get_json()['run_id']
    run = menu_client.get(f'/api/v1/fudo/sync/runs/{run_id}', headers=admin_headers).get_json()
    assert run['status'] == 'ok'
    assert run['stats']['created'] == 1
    assert run['params'] == {'start_date': '2026-10-01', 'end_date': '2026-10-31'}
    assert run_inline['client'].calls == [('2026-10-01', '2026-10-31')]
    assert Expense.query.count() == 1


@pytest.mark.parametrize('query', [
    '', 'start_date=2026-10-01', 'start_date=01/10/2026&end_date=2026-10-31',
    'start_date=2026-10-31&end_date=2026-10-01', 'start_date=2025-01-01&end_date=2026-10-31',
])
def test_post_rejects_bad_ranges(menu_client, admin_headers, run_inline, query):
    response = menu_client.post(f'{URL}?{query}', headers=admin_headers)

    assert response.status_code == 400
    assert response.get_json()['error']
    assert FudoSyncRun.query.count() == 0


def test_post_conflicts_with_running_sync(menu_client, admin_headers, run_inline):
    running = fudo_sync_runs.start_run('expenses', {})

    response = menu_client.post(f'{URL}?start_date=2026-10-01&end_date=2026-10-31', headers=admin_headers)

    assert response.status_code == 409
    assert response.get_json()['run_id'] == running.id


def test_post_requires_admin(menu_client, employee_headers, run_inline):
    response = menu_client.post(f'{URL}?start_date=2026-10-01&end_date=2026-10-31', headers=employee_headers)
    assert response.status_code == 403


def test_list_runs_newest_first(menu_client, admin_headers):
    base = datetime(2026, 10, 15, 12, 0)
    for minutes in (0, 40, 80):
        run = fudo_sync_runs.start_run('expenses', {}, now=base + timedelta(minutes=minutes))
        fudo_sync_runs.finish_run(run.id, stats={'created': minutes})

    runs = menu_client.get('/api/v1/fudo/sync/runs?kind=expenses&limit=2', headers=admin_headers).get_json()['runs']

    assert [r['stats']['created'] for r in runs] == [80, 40]


def test_get_unknown_run_is_404(menu_client, admin_headers):
    assert menu_client.get('/api/v1/fudo/sync/runs/999', headers=admin_headers).status_code == 404


def test_get_reports_stale_running_run_as_abandoned(menu_client, admin_headers):
    stale = fudo_sync_runs.start_run('expenses', {}, now=datetime.utcnow() - timedelta(minutes=31))

    run = menu_client.get(f'/api/v1/fudo/sync/runs/{stale.id}', headers=admin_headers).get_json()
    listed = menu_client.get('/api/v1/fudo/sync/runs?kind=expenses', headers=admin_headers).get_json()['runs']

    assert run['status'] == 'error'
    assert 'abandonada' in run['error']
    assert listed[0]['status'] == 'error'


def test_get_keeps_recent_running_run(menu_client, admin_headers):
    recent = fudo_sync_runs.start_run('expenses', {})

    run = menu_client.get(f'/api/v1/fudo/sync/runs/{recent.id}', headers=admin_headers).get_json()

    assert run['status'] == 'running'
