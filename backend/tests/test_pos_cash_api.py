from datetime import date, timedelta

from app.extensions import db
from app.models import ExpenseCategory
from cash_helpers import make_register
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401

BASE = '/api/v1/pos/cash'


def _setup(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    register = make_register()
    return client, auth_headers(client, cashier), cat, register


def test_registers_visible_to_waiters_but_cash_ops_are_not(pos_app):
    client, _headers, _cat, register = _setup(pos_app)
    waiter = auth_headers(client, make_user('mozo@test.com', modules=('Camarero',)))
    data = client.get(f'{BASE}/registers', headers=waiter).get_json()
    assert data['registers'] == [{'id': register.id, 'name': 'Caja principal', 'position': 0, 'open_session': None}]
    assert client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': 0},
                       headers=waiter).status_code == 403
    assert client.get(f'{BASE}/sessions', headers=waiter).status_code == 403


def test_open_movement_and_detail(pos_app):
    client, headers, cat, register = _setup(pos_app)
    category = ExpenseCategory(name='Insumos')
    db.session.add(category)
    db.session.commit()
    opened = client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': '1000'},
                         headers=headers)
    assert opened.status_code == 200
    session = opened.get_json()
    assert session['status'] == 'open' and session['opening_float'] == 1000.0
    assert session['summary']['cash']['expected'] == 1000.0
    again = client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': 0}, headers=headers)
    assert again.status_code == 409
    moved = client.post(f"{BASE}/sessions/{session['id']}/movements",
                        json={'kind': 'expense', 'amount': 200, 'reason': 'Hielo', 'category_id': category.id},
                        headers=headers).get_json()
    assert moved['summary']['cash']['expected'] == 800.0 and moved['movements'][-1]['kind'] == 'expense'
    detail = client.get(f"{BASE}/sessions/{session['id']}", headers=headers).get_json()
    assert [e['kind'] for e in detail['events']] == ['opened', 'movement_added']
    registers = client.get(f'{BASE}/registers', headers=headers).get_json()['registers']
    assert registers[0]['open_session']['id'] == session['id']
    current = client.get(f'{BASE}/sessions/current?register_id={register.id}', headers=headers)
    assert current.status_code == 200 and current.get_json()['id'] == session['id']
    bad = client.post(f"{BASE}/sessions/{session['id']}/movements",
                      json={'kind': 'deposit', 'amount': 'x', 'reason': 'a'}, headers=headers)
    assert bad.status_code == 400


def test_admin_only_endpoints(pos_app):
    client, headers, cat, register = _setup(pos_app)
    session = client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': 0},
                          headers=headers).get_json()
    deposit = client.post(f"{BASE}/sessions/{session['id']}/movements",
                          json={'kind': 'deposit', 'amount': 50, 'reason': 'Cambio'}, headers=headers).get_json()
    movement_id = deposit['movements'][-1]['id']
    assert client.post(f'{BASE}/movements/{movement_id}/cancel', json={'reason': 'x'},
                       headers=headers).status_code == 403
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    cancelled = client.post(f'{BASE}/movements/{movement_id}/cancel', json={'reason': 'Error'}, headers=admin)
    assert cancelled.status_code == 200 and cancelled.get_json()['summary']['cash']['expected'] == 0.0
    closed = client.post(f"{BASE}/sessions/{session['id']}/close",
                         json={'counts': [{'payment_method_id': cat.efectivo.id, 'counted': 0}]}, headers=headers)
    assert closed.status_code == 200 and closed.get_json()['status'] == 'closed'
    assert client.post(f"{BASE}/sessions/{session['id']}/reopen", json={'reason': 'x'},
                       headers=headers).status_code == 403
    assert client.post(f"{BASE}/sessions/{session['id']}/reopen", json={'reason': 'x'},
                       headers=admin).get_json()['status'] == 'open'


def test_close_conflict_reports_open_sales(pos_app):
    client, headers, cat, register = _setup(pos_app)
    _salon, t1, _t2 = make_floor()
    session = client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': 0},
                          headers=headers).get_json()
    client.post('/api/v1/pos/sales', json={'sale_type': 'salon', 'table_id': t1.id, 'people': 1}, headers=headers)
    response = client.post(f"{BASE}/sessions/{session['id']}/close",
                           json={'counts': [{'payment_method_id': cat.efectivo.id, 'counted': 0}]}, headers=headers)
    assert response.status_code == 409 and response.get_json()['open_sales'] == 1


def test_history_unassigned_and_categories(pos_app):
    client, headers, _cat, register = _setup(pos_app)
    db.session.add_all([ExpenseCategory(name='Insumos'), ExpenseCategory(name='Vieja', is_active=False)])
    db.session.commit()
    client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': 0}, headers=headers)
    day = date.today()
    params = f'from={(day - timedelta(days=1)).isoformat()}&to={(day + timedelta(days=1)).isoformat()}'
    history = client.get(f'{BASE}/sessions?{params}', headers=headers).get_json()
    assert history['total'] == 1 and history['sessions'][0]['status'] == 'open'
    assert client.get(f'{BASE}/sessions?from=ayer', headers=headers).status_code == 400
    assert client.get(f'{BASE}/unassigned-payments?{params}', headers=headers).get_json() == {'payments': []}
    categories = client.get(f'{BASE}/expense-categories', headers=headers).get_json()['categories']
    assert [c['name'] for c in categories] == ['Insumos']


def test_changes_reports_cash_version(pos_app):
    client, headers, _cat, register = _setup(pos_app)
    first = client.get('/api/v1/pos/changes', headers=headers).get_json()
    assert first['cash_version'] == 0
    client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': 0}, headers=headers)
    second = client.get(f"/api/v1/pos/changes?since={first['last_event_id']}", headers=headers).get_json()
    assert second['cash_version'] > 0
