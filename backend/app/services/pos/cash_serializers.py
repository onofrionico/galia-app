"""JSON de la caja: sesión, movimiento, conteo y evento."""
from app.services.pos.common import display_name
from app.services.pos.serializers import _iso, _money


def person(user):
    return {'id': user.id, 'name': display_name(user)} if user is not None else None


def movement_to_dict(movement):
    return {'id': movement.id, 'kind': movement.kind, 'amount': _money(movement.amount), 'reason': movement.reason,
            'expense_id': movement.expense_id, 'created_by': person(movement.creator),
            'created_at': _iso(movement.created_at), 'cancelled_at': _iso(movement.cancelled_at),
            'cancel_reason': movement.cancel_reason, 'is_active': movement.is_active}


def count_to_dict(count):
    return {'payment_method_id': count.payment_method_id, 'method_name': count.method_name,
            'expected': _money(count.expected), 'counted': _money(count.counted),
            'difference': _money(count.difference)}


def event_to_dict(event):
    return {'id': event.id, 'kind': event.kind, 'user': person(event.user), 'created_at': _iso(event.created_at),
            'payload': event.payload}


def session_to_dict(session, summary, events=None):
    data = {
        'id': session.id, 'register': {'id': session.register.id, 'name': session.register.name},
        'status': session.status, 'opened_at': _iso(session.opened_at), 'opened_by': person(session.opener),
        'opening_float': _money(session.opening_float), 'closed_at': _iso(session.closed_at),
        'closed_by': person(session.closer), 'closing_note': session.closing_note, 'summary': summary,
        'movements': [movement_to_dict(m) for m in session.movements],
        'counts': [count_to_dict(c) for c in session.counts],
    }
    if events is not None:
        data['events'] = [event_to_dict(e) for e in events]
    return data


def register_to_dict(register, open_session):
    return {'id': register.id, 'name': register.name, 'position': register.position,
            'open_session': ({'id': open_session.id, 'opened_at': _iso(open_session.opened_at),
                              'opened_by': person(open_session.opener)} if open_session else None)}
