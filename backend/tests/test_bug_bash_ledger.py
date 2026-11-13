"""Regresiones del bug bash 2026-11: borrado logico de gastos/ventas y estadisticas de ventas."""
from datetime import date, datetime
from decimal import Decimal

from app.extensions import db
from app.models.expense import Expense
from app.models.pos.cash import CashMovement, CashRegister, CashSession
from app.models.sale import Sale
from app.models.user import User


def _expense(importe='5000', **extra):
    expense = Expense(fecha=date(2026, 3, 4), importe=Decimal(importe), cancelado=False, **extra)
    db.session.add(expense)
    db.session.commit()
    return expense


def _sale(total, estado='Cerrada', source='fudo', tipo='Local'):
    sale = Sale(fecha=date(2026, 3, 4), creacion=datetime(2026, 3, 4, 12, 0), estado=estado,
                total=Decimal(total), source=source, tipo_venta=tipo)
    db.session.add(sale)
    db.session.commit()
    return sale


# --- 6. Borrado logico -----------------------------------------------------------------------------

def test_delete_expense_is_logical(menu_client, admin_headers):
    expense = _expense()
    response = menu_client.delete(f'/api/v1/expenses/{expense.id}', headers=admin_headers)
    assert response.status_code == 200
    db.session.expire_all()
    kept = db.session.get(Expense, expense.id)
    assert kept is not None and kept.cancelado is True


def test_delete_expense_linked_to_cash_movement_is_rejected(menu_client, admin_headers):
    expense = _expense()
    admin = User.query.filter_by(role='admin').first()
    register = CashRegister(name='Caja 1')
    db.session.add(register)
    db.session.flush()
    session = CashSession(register_id=register.id, opened_at=datetime(2026, 3, 4, 8), opened_by=admin.id,
                          opening_float=Decimal('0'))
    db.session.add(session)
    db.session.flush()
    db.session.add(CashMovement(session_id=session.id, kind='expense', amount=Decimal('5000'),
                                expense_id=expense.id, created_by=admin.id, created_at=datetime(2026, 3, 4, 9)))
    db.session.commit()
    response = menu_client.delete(f'/api/v1/expenses/{expense.id}', headers=admin_headers)
    assert response.status_code == 409
    db.session.expire_all()
    assert db.session.get(Expense, expense.id).cancelado is False


def test_delete_sale_is_logical(menu_client, admin_headers):
    sale = _sale('1000')
    response = menu_client.delete(f'/api/v1/sales/{sale.id}', headers=admin_headers)
    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Sale, sale.id).estado == 'Cancelada'


def test_delete_sale_from_pos_is_still_rejected(menu_client, admin_headers):
    sale = _sale('1000', source='galia')
    assert menu_client.delete(f'/api/v1/sales/{sale.id}', headers=admin_headers).status_code == 409
    db.session.expire_all()
    assert db.session.get(Sale, sale.id).estado == 'Cerrada'


# --- 7. Estadisticas sin canceladas ----------------------------------------------------------------

def test_sales_stats_exclude_cancelled_from_totals(menu_client, admin_headers):
    _sale('1000')
    _sale('500')
    _sale('9999', estado='Cancelada')
    body = menu_client.get('/api/v1/sales/stats', headers=admin_headers).get_json()
    assert body['total_ventas'] == 2
    assert body['total_monto'] == 1500.0
    assert sum(t['cantidad'] for t in body['por_tipo']) == 2
    assert sum(m['total'] for m in body['por_medio_pago']) == 1500.0
    # el desglose por estado si muestra las canceladas
    por_estado = {e['estado']: e for e in body['por_estado']}
    assert por_estado['Cancelada']['cantidad'] == 1 and por_estado['Cancelada']['total'] == 9999.0
    assert por_estado['Cerrada']['cantidad'] == 2
