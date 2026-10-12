"""Motivo de una anulación: uno del catálogo, texto libre o ambos."""
from app.extensions import db
from app.models.pos import CancelReason
from app.services.pos.common import parse_id, require_reason
from app.services.pos.errors import bad_request
from app.utils.validation import clean_str

MAX_REASON_LENGTH = 255


def resolve_reason(reason_id, reason):
    """Devuelve (texto, id) del motivo.

    Con `reason_id` (un motivo activo del catálogo) el texto es su nombre, más el detalle libre si viene.
    Sin `reason_id`, el texto libre es obligatorio.
    """
    if reason_id is None:
        return require_reason(reason), None
    found = db.session.get(CancelReason, parse_id(reason_id, 'El motivo'))
    if found is None or not found.is_active:
        raise bad_request('El motivo no existe')
    detail = clean_str(reason, MAX_REASON_LENGTH)
    text = f'{found.name} — {detail}' if detail else found.name
    return text[:MAX_REASON_LENGTH], found.id
