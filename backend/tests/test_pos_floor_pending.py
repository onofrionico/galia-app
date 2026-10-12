from sqlalchemy import event

from app.extensions import db
from app.services.pos import sale_service
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _floor_sales(client, headers):
    data = client.get('/api/v1/pos/floor', headers=headers).get_json()
    return {sale['id']: sale for table in data['tables'] for sale in table['sales']}


def test_floor_counts_pending_items_per_sale(pos_app):
    client = pos_app.test_client()
    boss = make_user('jefe@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _s, t1, t2 = make_floor()
    # Mesa 1: una venta con un ítem confirmado y dos pendientes.
    first = sale_service.open_sale(boss, 'salon', table_id=t1.id, people=2)
    sale_service.add_item(boss, first.id, cat.unidad.id)
    sale_service.confirm_batch(boss, first.id)
    sale_service.add_item(boss, first.id, cat.unidad.id)
    sale_service.add_item(boss, first.id, cat.unidad.id)
    # Mesa 2: dos confirmados, uno anulado; ninguno pendiente.
    second = sale_service.open_sale(boss, 'salon', table_id=t2.id, people=1)
    sale_service.add_item(boss, second.id, cat.unidad.id)
    sale_service.add_item(boss, second.id, cat.unidad.id)
    second = sale_service.confirm_batch(boss, second.id)
    sale_service.cancel_item(boss, second.id, second.items[0].id, 'Error de carga')

    sales = _floor_sales(client, auth_headers(client, boss))
    assert sales[first.id]['pending_count'] == 2
    assert sales[second.id]['pending_count'] == 0


def test_floor_counts_each_account_of_a_split_table(pos_app):
    client = pos_app.test_client()
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t2 = make_floor()
    original = sale_service.open_sale(boss, 'salon', table_id=t1.id, people=2)
    sale_service.add_item(boss, original.id, cat.unidad.id)
    original = sale_service.confirm_batch(boss, original.id)
    confirmed_id = original.items[0].id
    sale_service.add_item(boss, original.id, cat.unidad.id)
    other = sale_service.split_sale(boss, original.id, [{'item_id': confirmed_id, 'quantity': 1}])
    sale_service.reopen(boss, other.id)
    sale_service.add_item(boss, other.id, cat.unidad.id)
    sale_service.add_item(boss, other.id, cat.unidad.id)

    sales = _floor_sales(client, auth_headers(client, boss))
    assert sales[original.id]['pending_count'] == 1
    assert sales[other.id]['pending_count'] == 2


def test_floor_counts_pending_with_a_single_grouped_query(pos_app):
    client = pos_app.test_client()
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, t2 = make_floor()
    for table in (t1, t2):
        sale = sale_service.open_sale(boss, 'salon', table_id=table.id, people=1)
        sale_service.add_item(boss, sale.id, cat.unidad.id)
    headers = auth_headers(client, boss)
    statements = []

    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(db.engine, 'before_cursor_execute', capture)
    try:
        client.get('/api/v1/pos/floor', headers=headers)
    finally:
        event.remove(db.engine, 'before_cursor_execute', capture)
    grouped = [s for s in statements if 'pos_sale_items' in s and 'GROUP BY' in s.upper()]
    assert len(grouped) == 1


def test_floor_without_sales_still_works(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    make_floor()
    data = client.get('/api/v1/pos/floor', headers=auth_headers(client, waiter)).get_json()
    assert all(table['sales'] == [] for table in data['tables'])
