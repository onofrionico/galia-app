from datetime import date
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import FudoImportMonth, Sale, SaleItem
from app.services import cutover, fudo_sales_import
from app.utils.fudo_client import FudoClient
from fudo_sale_fakes import FakeSalesClient, fudo_category, fudo_item, fudo_product, fudo_sale
from pos_helpers import auth_headers, make_user, pos_app  # noqa: F401

SEP = date(2026, 9, 1)
CATALOG = [fudo_category(5, 'Panadería'), fudo_product(77, 'Medialuna', 5), fudo_product(78, 'Latte', 5)]


def _sale(sale_id, total=1800, state='CLOSED', day='2026-09-10T15:00:00Z', items=None):
    items = items if items is not None else [fudo_item(f'{sale_id}1', 77, 2, 900)]
    return fudo_sale(sale_id, day, total, state=state, items=items)


def test_import_month_creates_sales_with_items(pos_app):
    client = FakeSalesClient({'2026-09': [_sale(1), _sale(2, total=900, items=[fudo_item('21', 78, 1, 900)])]},
                             included=CATALOG)
    result = fudo_sales_import.import_month(client, SEP)
    assert Sale.query.count() == 2 and SaleItem.query.count() == 2
    assert {s.source for s in Sale.query} == {'fudo'}
    month = db.session.get(FudoImportMonth, SEP)
    assert month.status == 'done' and month.matches
    assert result['fudo_count'] == result['galia_count'] == 2 and result['fudo_total'] == '2700.00'


def test_import_month_paginates(pos_app):
    sales = [_sale(1000 + i, total=900, items=[fudo_item(f'i{i}', 77, 1, 900)]) for i in range(503)]
    result = fudo_sales_import.import_month(FakeSalesClient({'2026-09': sales}, included=CATALOG), SEP)
    assert result['fudo_count'] == result['galia_count'] == 503 and result['matches']


def test_client_reads_every_page(monkeypatch):
    pages = {1: [{'id': str(i)} for i in range(500)], 2: [{'id': 'x'}, {'id': 'y'}, {'id': 'z'}]}
    calls = []

    def fake_get_sales(self, page_size=500, page_number=1, filters=None, extra_params=None):
        calls.append(filters)
        return {'data': pages[page_number], 'included': []}

    monkeypatch.setattr(FudoClient, 'get_sales', fake_get_sales)
    client = FudoClient.__new__(FudoClient)
    payload = client.get_all_sales_with_included('2026-09-01T03:00:00Z', '2026-10-01T02:59:59Z',
                                                 states=('CLOSED', 'CANCELED'))
    assert len(payload['data']) == 503
    assert calls[0]['saleState'] == 'in.(CLOSED,CANCELED)'


def test_import_twice_is_idempotent(pos_app):
    client = FakeSalesClient({'2026-09': [_sale(1), _sale(2)]}, included=CATALOG)
    fudo_sales_import.import_month(client, SEP)
    result = fudo_sales_import.import_month(client, SEP)
    assert Sale.query.count() == 2 and SaleItem.query.count() == 2 and result['changed'] == 0


def test_reimport_updates_cancelled_sale(pos_app):
    first = FakeSalesClient({'2026-09': [_sale(1), _sale(2)]}, included=CATALOG)
    fudo_sales_import.import_month(first, SEP)
    later = FakeSalesClient({'2026-09': [_sale(1), _sale(2, state='CANCELED')]}, included=CATALOG)
    result = fudo_sales_import.import_month(later, SEP)
    assert Sale.query.filter_by(external_id=2).one().estado == 'Cancelada'
    assert result['changed'] == 1 and result['galia_count'] == 1 and result['fudo_count'] == 1


def test_bad_sale_does_not_stop_month(pos_app):
    broken = _sale(3)
    broken['id'] = 'no-es-un-numero'
    client = FakeSalesClient({'2026-09': [_sale(1), broken]}, included=CATALOG)
    result = fudo_sales_import.import_month(client, SEP)
    assert Sale.query.count() == 1 and len(result['errors']) == 1


def test_history_resumes_and_skips_done_months(pos_app, monkeypatch):
    monkeypatch.setattr(fudo_sales_import, 'current_month', lambda: date(2026, 9, 1))
    db.session.add(FudoImportMonth(month=date(2026, 6, 1), status='done', fudo_count=0, galia_count=0,
                                   fudo_total=0, galia_total=0, changed=0))
    db.session.commit()
    client = FakeSalesClient({'2026-07': [_sale(1, day='2026-07-10T15:00:00Z')]}, first=date(2026, 6, 15),
                             included=CATALOG)
    result = fudo_sales_import.import_history(client)
    assert client.requested == ['2026-07', '2026-08', '2026-09']
    assert [m['month'] for m in result['months']] == ['2026-07', '2026-08', '2026-09']
    fudo_sales_import.import_history(client, force=True)
    assert client.requested[-4:] == ['2026-06', '2026-07', '2026-08', '2026-09']


def test_history_route_blocked_when_fudo_off(pos_app):
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('admin@test.com', role='admin'))
    settings = cutover.get_settings()
    settings.catalog_in_galia = settings.fudo_off = True
    db.session.commit()
    response = client.post('/api/v1/fudo/sync/sales/history', headers=headers)
    assert response.status_code == 409 and response.get_json()['error'] == 'Fudo está apagado'
    assert client.post('/api/v1/fudo/sync/sales?start_date=2026-09-01&end_date=2026-09-30',
                       headers=headers).status_code == 409


def test_months_route_lists_newest_first(pos_app):
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('admin@test.com', role='admin'))
    fudo_sales_import.import_month(FakeSalesClient({'2026-09': [_sale(1)]}, included=CATALOG), SEP)
    fudo_sales_import.import_month(FakeSalesClient({}, included=CATALOG), date(2026, 10, 1))
    months = client.get('/api/v1/fudo/import/months', headers=headers).get_json()['months']
    assert [m['month'] for m in months] == ['2026-10', '2026-09'] and months[1]['matches'] is True
