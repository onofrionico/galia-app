from app.extensions import db
from app.models.pos import CancelReason, PosPayment, PosSale, PosSaleItem
from pos_helpers import pos_app  # noqa: F401


def test_cancel_reason_model(pos_app):
    reason = CancelReason(name='Error de carga', position=1)
    db.session.add(reason)
    db.session.commit()
    assert reason.to_dict() == {'id': reason.id, 'name': 'Error de carga', 'position': 1, 'is_active': True}


def test_cancellable_rows_have_reason_id_column():
    for model in (PosSale, PosSaleItem, PosPayment):
        assert 'cancel_reason_id' in model.__table__.columns
