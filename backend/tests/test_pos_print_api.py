from app.extensions import db
from app.models.pos import PrintPoint
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401
from print_helpers import make_printer, make_station

BASE = '/api/v1/pos'


def _billed_sale(client, headers, table, cat):
    sale = client.post(f'{BASE}/sales', json={'sale_type': 'salon', 'table_id': table.id, 'people': 1},
                       headers=headers).get_json()
    client.post(f"{BASE}/sales/{sale['id']}/items", json={'product_variant_id': cat.unidad.id}, headers=headers)
    client.post(f"{BASE}/sales/{sale['id']}/confirm", headers=headers)
    client.post(f"{BASE}/sales/{sale['id']}/request-bill", headers=headers)
    return sale


def test_waiter_prints_bill_but_cannot_touch_the_queue(pos_app):
    client = pos_app.test_client()
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    make_printer('Térmica caja', cashier=True)
    waiter = auth_headers(client, make_user('mozo@test.com', modules=('Camarero',)))
    sale = _billed_sale(client, waiter, t1, cat)
    bill = client.post(f"{BASE}/sales/{sale['id']}/print/bill", headers=waiter)
    assert bill.status_code == 200 and bill.get_json()['kind'] == 'bill'
    jobs = client.get(f"{BASE}/sales/{sale['id']}/print-jobs", headers=waiter).get_json()['jobs']
    assert [j['kind'] for j in jobs] == ['bill']
    assert client.post(f"{BASE}/print/jobs/{jobs[0]['id']}/reprint", headers=waiter).status_code == 200
    assert client.post(f'{BASE}/print/claim', json={'print_point': 'Caja'}, headers=waiter).status_code == 403
    assert client.get(f'{BASE}/print/status', headers=waiter).status_code == 403


def test_queue_flow_through_the_api(pos_app):
    client = pos_app.test_client()
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    printer = make_printer('Térmica caja', cashier=True)
    headers = auth_headers(client, make_user('caja@test.com', modules=('POS',)))
    sale = _billed_sale(client, headers, t1, cat)
    client.post(f"{BASE}/sales/{sale['id']}/print/bill", headers=headers)
    claimed = client.post(f'{BASE}/print/claim', json={'print_point': 'Caja'}, headers=headers).get_json()['jobs']
    assert claimed[0]['printer']['host'] == '192.168.0.50' and claimed[0]['status'] == 'printing'
    failed = client.post(f"{BASE}/print/jobs/{claimed[0]['id']}/failed", json={'error': 'Sin papel'}, headers=headers)
    assert failed.get_json()['status'] == 'failed'
    assert client.post(f"{BASE}/print/jobs/{claimed[0]['id']}/retry", headers=headers).get_json()['status'] == 'pending'
    marked = client.post(f"{BASE}/print/jobs/{claimed[0]['id']}/mark-printed", headers=headers).get_json()
    assert marked['status'] == 'printed'
    status = client.get(f'{BASE}/print/status', headers=headers).get_json()
    assert status['pending'] == 0 and status['points'][0]['name'] == 'Caja'
    points = client.get(f'{BASE}/print/points', headers=headers).get_json()['points']
    assert points[0]['printers'][0]['id'] == printer.id
    test_job = client.post(f'{BASE}/print/printers/{printer.id}/test', headers=headers).get_json()
    assert test_job['kind'] == 'test'
    assert client.post(f'{BASE}/print/claim', json={}, headers=headers).status_code == 400


def test_receipt_conflict_and_qz_signing(pos_app, monkeypatch):
    monkeypatch.delenv('QZ_CERTIFICATE', raising=False)
    monkeypatch.delenv('QZ_PRIVATE_KEY', raising=False)
    client = pos_app.test_client()
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    headers = auth_headers(client, make_user('caja@test.com', modules=('POS',)))
    sale = _billed_sale(client, headers, t1, cat)
    response = client.post(f"{BASE}/sales/{sale['id']}/print/receipt", headers=headers)
    assert response.status_code == 409
    certificate = client.get(f'{BASE}/print/qz-certificate', headers=headers)
    assert certificate.status_code == 200 and 'BEGIN CERTIFICATE' in certificate.get_json()['certificate']
    assert client.post(f'{BASE}/print/qz-sign', json={'request': 'x'}, headers=headers).status_code == 200
    assert client.post(f'{BASE}/print/qz-sign', json={}, headers=headers).status_code == 400


def test_qz_setup_script_installs_the_certificate(pos_app, monkeypatch):
    monkeypatch.delenv('QZ_CERTIFICATE', raising=False)
    monkeypatch.delenv('QZ_PRIVATE_KEY', raising=False)
    client = pos_app.test_client()
    waiter = auth_headers(client, make_user('mozo@test.com', modules=('Camarero',)))
    assert client.get(f'{BASE}/print/qz-setup', headers=waiter).status_code == 403
    headers = auth_headers(client, make_user('caja@test.com', modules=('POS',)))
    response = client.get(f'{BASE}/print/qz-setup', headers=headers)
    assert response.status_code == 200
    assert 'attachment' in response.headers['Content-Disposition']
    assert 'preparar-impresion-galia.bat' in response.headers['Content-Disposition']
    script = response.get_data(as_text=True)
    certificate = client.get(f'{BASE}/print/qz-certificate', headers=headers).get_json()['certificate']
    # Cada renglón del certificado se escribe en override.crt, y el script usa fin de línea de Windows.
    for line in certificate.strip().splitlines():
        assert f'echo {line}' in script
    assert 'override.crt' in script and '-Verb RunAs' in script and 'qz-tray.exe' in script
    assert '\r\n' in script and '\n' not in script.replace('\r\n', '')


def test_stations_lookup_for_products_users(pos_app):
    client = pos_app.test_client()
    make_station('Cocina')
    inactive = make_station('Vieja')
    inactive.is_active = False
    db.session.commit()
    headers = auth_headers(client, make_user('prod@test.com', modules=('Products',)))
    stations = client.get(f'{BASE}/print/stations', headers=headers).get_json()['stations']
    assert [s['name'] for s in stations] == ['Cocina']


def test_config_is_admin_only_and_validates_printers(pos_app):
    client = pos_app.test_client()
    cashier_headers = auth_headers(client, make_user('caja@test.com', modules=('POS',)))
    assert client.get(f'{BASE}/config/printers', headers=cashier_headers).status_code == 403
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    station = client.post(f'{BASE}/config/print-stations', json={'name': 'Cocina'}, headers=admin)
    assert station.status_code == 201
    station_id = station.get_json()['id']
    ok = client.post(f'{BASE}/config/printers', json={
        'name': 'Térmica cocina', 'connection': 'network', 'host': '192.168.0.60', 'port': 9100, 'paper_width': 80,
        'print_point': 'Caja', 'station_id': station_id, 'is_cashier': False, 'is_active': True}, headers=admin)
    assert ok.status_code == 201 and ok.get_json()['station_name'] == 'Cocina'
    assert db.session.get(PrintPoint, 'Caja') is not None
    bad_cases = [
        {'name': 'A', 'connection': 'network', 'paper_width': 80, 'print_point': 'Caja'},
        {'name': 'B', 'connection': 'usb', 'paper_width': 80, 'print_point': 'Caja'},
        {'name': 'C', 'connection': 'network', 'host': 'h', 'paper_width': 70, 'print_point': 'Caja'},
        {'name': 'D', 'connection': 'network', 'host': 'h', 'paper_width': 80, 'print_point': ''},
        {'name': 'E', 'connection': 'network', 'host': 'h', 'paper_width': 80, 'print_point': 'Caja',
         'station_id': station_id},
        {'name': 'F', 'connection': 'network', 'host': 'h', 'paper_width': 80, 'print_point': 'Caja',
         'station_id': station_id, 'is_cashier': True},
    ]
    for body in bad_cases:
        assert client.post(f'{BASE}/config/printers', json=body, headers=admin).status_code == 400, body
    cashier = client.post(f'{BASE}/config/printers', json={
        'name': 'Térmica caja', 'connection': 'usb', 'os_name': 'EPSON', 'paper_width': 58, 'print_point': 'Caja',
        'is_cashier': True}, headers=admin)
    assert cashier.status_code == 201
    second = client.post(f'{BASE}/config/printers', json={
        'name': 'Otra caja', 'connection': 'usb', 'os_name': 'X', 'paper_width': 58, 'print_point': 'Caja',
        'is_cashier': True}, headers=admin)
    assert second.status_code == 400
    printer_id = ok.get_json()['id']
    updated = client.put(f'{BASE}/config/printers/{printer_id}', json={'print_point': 'Oficina'}, headers=admin)
    assert updated.status_code == 200 and updated.get_json()['print_point'] == 'Oficina'
    assert db.session.get(PrintPoint, 'Oficina') is not None
    listed = client.get(f'{BASE}/config/printers', headers=admin).get_json()['printers']
    assert len(listed) == 2
    stations = client.get(f'{BASE}/config/print-stations', headers=admin).get_json()['print_stations']
    assert [s['name'] for s in stations] == ['Cocina']
