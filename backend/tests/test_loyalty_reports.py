from datetime import date, datetime, timedelta
from decimal import Decimal

from app.extensions import db
from app.models import Sale
from app.models.loyalty import LoyaltyMovement, LoyaltySettings
from app.models.pos import PosSale
from app.services.loyalty import reports
from loyalty_helpers import auth_headers, make_catalog, make_customer, make_reward, make_user, pos_app  # noqa: F401

TODAY = date(2026, 11, 30)


def _visit(customer, cashier, day, total='1000', practice=False, number=[0]):
    number[0] += 1
    sale_row = None
    if not practice:
        sale_row = Sale(fecha=day, creacion=datetime.combine(day, datetime.min.time()), estado='Cerrada',
                        total=Decimal(total), source='galia', tipo_venta='Local')
        db.session.add(sale_row)
        db.session.flush()
    pos = PosSale(business_date=day, number=number[0], sale_type='counter', status='closed',
                  opened_at=datetime.combine(day, datetime.min.time()), opened_by=cashier.id,
                  closed_at=datetime.combine(day, datetime.min.time()), total=Decimal(total),
                  customer_id=customer.id if customer else None, is_practice=practice,
                  sale_id=sale_row.id if sale_row else None)
    db.session.add(pos)
    db.session.commit()
    return pos


def _fudo_sale(day, total):
    db.session.add(Sale(fecha=day, creacion=datetime.combine(day, datetime.min.time()), estado='Cerrada',
                        total=Decimal(total), source='fudo', tipo_venta='Local'))
    db.session.commit()


def test_active_uses_configured_period(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    recent = make_customer()
    old = make_customer(first='Juan', last='Gómez', email='juan@test.com')
    _visit(recent, cashier, TODAY - timedelta(days=10))
    _visit(recent, cashier, TODAY - timedelta(days=3))
    _visit(old, cashier, TODAY - timedelta(days=40))
    active = reports.active_customers(TODAY)
    assert [(a['id'], a['visits'], a['last_visit']) for a in active] == [
        (recent.id, 2, (TODAY - timedelta(days=3)).isoformat())]
    assert [i['id'] for i in reports.inactive_customers(TODAY)] == [old.id]
    LoyaltySettings.get().active_days = 45
    db.session.commit()
    assert {a['id'] for a in reports.active_customers(TODAY)} == {recent.id, old.id}


def test_inactive_includes_never_visited(pos_app):
    newbie = make_customer()
    rows = reports.inactive_customers(TODAY)
    assert rows == [{'id': newbie.id, 'full_name': 'Lucía Pérez', 'last_visit': None, 'never_visited': True}]


def test_practice_sales_excluded(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    customer = make_customer()
    _visit(customer, cashier, TODAY - timedelta(days=1), practice=True)
    assert reports.active_customers(TODAY) == []
    result = reports.registered_vs_unregistered(TODAY - timedelta(days=5), TODAY)
    assert result['registered']['count'] == 0


def test_redemptions_excludes_reversed_and_uses_frozen_values(pos_app):
    cat = make_catalog()
    customer = make_customer()
    cafe = make_reward(cat.taza, 8, name='Café gratis')
    focaccia = make_reward(cat.unidad, 10, name='Focaccia')
    day = datetime(2026, 11, 10, 12)

    def redeem(reward, cost, pesos):
        m = LoyaltyMovement(customer_id=customer.id, kind='redeem', amount=-cost, reward_id=reward.id,
                            reward_cost=cost, pesos_value=Decimal(pesos), created_at=day)
        db.session.add(m)
        db.session.flush()
        return m

    redeem(cafe, 8, '2000')
    redeem(cafe, 8, '2300')
    reversed_one = redeem(focaccia, 10, '4000')
    db.session.add(LoyaltyMovement(customer_id=customer.id, kind='redeem_reversal', amount=10,
                                   reversal_of_id=reversed_one.id, created_at=day))
    redeem(focaccia, 12, '4500')
    cafe.cost = 20
    db.session.commit()
    result = reports.redemptions(date(2026, 11, 1), date(2026, 11, 30))
    assert result['total'] == 3 and result['cafecitos'] == 28 and result['pesos'] == 8800.0
    assert result['by_reward'] == [
        {'reward': 'Café gratis', 'count': 2, 'cafecitos': 16, 'pesos': 4300.0},
        {'reward': 'Focaccia', 'count': 1, 'cafecitos': 12, 'pesos': 4500.0},
    ]
    assert reports.redemptions(date(2026, 12, 1), date(2026, 12, 31))['total'] == 0


def test_sales_comparison_counts_fudo_as_unregistered(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    customer = make_customer()
    day = date(2026, 11, 10)
    _visit(customer, cashier, day, total='3000')
    _visit(customer, cashier, day, total='1000')
    _visit(None, cashier, day, total='500')
    _fudo_sale(day, '1500')
    result = reports.registered_vs_unregistered(date(2026, 11, 1), date(2026, 11, 30))
    assert result['registered'] == {'total': 4000.0, 'count': 2, 'avg_ticket': 2000.0}
    assert result['unregistered'] == {'total': 2000.0, 'count': 2, 'avg_ticket': 1000.0}


def test_report_endpoints(pos_app):
    client = pos_app.test_client()
    manager = make_user('fide@test.com', modules=('Fidelizacion',))
    headers = auth_headers(client, manager)
    base = '/api/v1/loyalty/admin/reports'
    assert client.get(f'{base}/active', headers=headers).status_code == 200
    assert client.get(f'{base}/inactive', headers=headers).status_code == 200
    ok = client.get(f'{base}/redemptions?from=2026-11-01&to=2026-11-30', headers=headers)
    assert ok.status_code == 200 and ok.get_json()['total'] == 0
    assert client.get(f'{base}/sales-comparison?from=2026-11-01&to=2026-11-30', headers=headers).status_code == 200
    assert client.get(f'{base}/redemptions?from=mal', headers=headers).status_code == 400
