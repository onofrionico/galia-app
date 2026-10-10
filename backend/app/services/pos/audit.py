from datetime import datetime
from decimal import Decimal

from app.extensions import db
from app.models.pos import PosSaleEvent


def _jsonable(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def record(sale, user, event_type, item=None, item_id=None, **payload):
    """Registra un evento de auditoría en la transacción actual."""
    db.session.add(PosSaleEvent(
        sale_id=sale.id,
        item_id=item.id if item is not None else item_id,
        user_id=user.id,
        event_type=event_type,
        payload=_jsonable(payload),
        created_at=datetime.utcnow(),
    ))
