import pytest

from app.extensions import db
from app.models.pos import CancelReason, PosPayment, PosSale, PosSaleEvent, PosSaleItem
from app.services.pos import payment_service, sale_service
from app.services.pos.errors import PosError
from app.services.pos.serializers import sale_to_dict
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def test_cancel_reason_model(pos_app):
    reason = CancelReason(name='Error de carga', position=1)
    db.session.add(reason)
    db.session.commit()
    assert reason.to_dict() == {'id': reason.id, 'name': 'Error de carga', 'position': 1, 'is_active': True}


def test_cancellable_rows_have_reason_id_column():
    for model in (PosSale, PosSaleItem, PosPayment):
        assert 'cancel_reason_id' in model.__table__.columns



def _reason(name='Error de carga', active=True):
    reason = CancelReason(name=name, is_active=active)
    db.session.add(reason)
    db.session.commit()
    return reason


def _confirmed_sale(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=2)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=2)
    return sale_service.confirm_batch(user, sale.id)


def test_cancel_item_with_catalog_reason(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    reason = _reason()
    sale = _confirmed_sale(boss, cat, t1)
    sale = sale_service.cancel_item(boss, sale.id, sale.items[0].id, None, reason_id=reason.id)
    item = sale.items[0]
    assert item.cancel_reason == 'Error de carga' and item.cancel_reason_id == reason.id
    payload = PosSaleEvent.query.filter_by(event_type='item_cancelled').one().payload
    assert payload['reason'] == 'Error de carga' and payload['reason_id'] == reason.id


def test_catalog_reason_with_detail(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    reason = _reason()
    sale = _confirmed_sale(boss, cat, t1)
    sale = sale_service.cancel_item(boss, sale.id, sale.items[0].id, 'era de otra mesa', reason_id=reason.id)
    assert sale.items[0].cancel_reason == 'Error de carga — era de otra mesa'


def test_free_text_reason_still_works(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed_sale(boss, cat, t1)
    sale = sale_service.cancel_item(boss, sale.id, sale.items[0].id, 'Se cayó')
    assert sale.items[0].cancel_reason == 'Se cayó' and sale.items[0].cancel_reason_id is None


@pytest.mark.parametrize('reason', [None, '   '])
def test_reason_is_required_without_catalog_reason(pos_app, reason):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed_sale(boss, cat, t1)
    with pytest.raises(PosError) as exc:
        sale_service.cancel_item(boss, sale.id, sale.items[0].id, reason)
    assert exc.value.status == 400


def test_inactive_or_missing_reason_is_rejected(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    inactive = _reason('Viejo', active=False)
    sale = _confirmed_sale(boss, cat, t1)
    for reason_id in (inactive.id, 9999):
        with pytest.raises(PosError) as exc:
            sale_service.cancel_item(boss, sale.id, sale.items[0].id, None, reason_id=reason_id)
        assert exc.value.status == 400 and exc.value.message == 'El motivo no existe'


def test_cancel_payment_and_sale_store_reason_id(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    reason = _reason()
    sale = _confirmed_sale(boss, cat, t1)
    sale_service.request_bill(boss, sale.id)
    sale = payment_service.add_payment(boss, sale.id, cat.debito.id, 500)
    sale = payment_service.cancel_payment(boss, sale.payments[0].id, None, reason_id=reason.id)
    assert sale.payments[0].cancel_reason_id == reason.id
    assert PosSaleEvent.query.filter_by(event_type='payment_cancelled').one().payload['reason_id'] == reason.id
    sale = sale_service.cancel_sale(boss, sale.id, None, reason_id=reason.id)
    assert sale.cancel_reason == 'Error de carga' and sale.cancel_reason_id == reason.id
    assert {i.cancel_reason_id for i in sale.items} == {reason.id}


def test_serialized_sale_exposes_reason_ids(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    reason = _reason()
    sale = _confirmed_sale(boss, cat, t1)
    sale = sale_service.cancel_sale(boss, sale.id, None, reason_id=reason.id)
    data = sale_to_dict(sale)
    assert data['cancel_reason_id'] == reason.id
    assert data['items'][0]['cancel_reason_id'] == reason.id
    assert data['payments'] == []
