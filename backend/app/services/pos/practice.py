"""Modo práctica: lo creado con el modo prendido queda marcado y nunca cuenta. "Borrar práctica" lo elimina."""
from app.extensions import db
from app.models.pos import (CashEvent, CashMovement, CashSession, CashSessionCount, PosDiscount, PosPayment, PosSale,
                            PosSaleEvent, PosSaleItem, PosSaleItemModifier, PrintJob)
from app.services import cutover
from app.services.pos.errors import PosError, forbidden


def is_practice_sale(sale):
    return bool(getattr(sale, 'is_practice', False))


def clear_practice(user):
    """Borra las ventas y cajas de práctica con todo lo que cuelga de ellas. Solo admin, con el modo apagado."""
    if getattr(user, 'role', None) != 'admin':
        raise forbidden('Solo un administrador borra la práctica')
    if cutover.practice_mode():
        raise PosError('Apagá el modo práctica antes de borrarla')
    sale_ids = [s.id for s in PosSale.query.filter_by(is_practice=True).with_entities(PosSale.id)]
    session_ids = [s.id for s in CashSession.query.filter_by(is_practice=True).with_entities(CashSession.id)]
    if sale_ids:
        item_ids = [i.id for i in PosSaleItem.query.filter(PosSaleItem.sale_id.in_(sale_ids))
                    .with_entities(PosSaleItem.id)]
        if item_ids:
            PosSaleItemModifier.query.filter(PosSaleItemModifier.item_id.in_(item_ids)).delete(
                synchronize_session=False)
        for model in (PosDiscount, PosPayment, PosSaleEvent, PrintJob, PosSaleItem):
            model.query.filter(model.sale_id.in_(sale_ids)).delete(synchronize_session=False)
        PosSale.query.filter(PosSale.id.in_(sale_ids)).update({PosSale.split_from_id: None},
                                                               synchronize_session=False)
        PosSale.query.filter(PosSale.id.in_(sale_ids)).delete(synchronize_session=False)
    if session_ids:
        for model in (CashMovement, CashSessionCount, CashEvent):
            model.query.filter(model.session_id.in_(session_ids)).delete(synchronize_session=False)
        CashSession.query.filter(CashSession.id.in_(session_ids)).delete(synchronize_session=False)
    db.session.commit()
    db.session.expire_all()
    return {'sales': len(sale_ids), 'cash_sessions': len(session_ids)}
