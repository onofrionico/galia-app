"""Rate limit por IP para endpoints públicos, en memoria y sin dependencias.

Es por proceso (cada worker de gunicorn cuenta aparte): alcanza para frenar un abuso casual que sature
los workers que también sirven el POS. Para algo más estricto, ponerlo en Cloudflare/Render.
"""
import threading
import time
from collections import deque
from functools import wraps

from flask import current_app, jsonify, request

_lock = threading.Lock()
_hits = {}
_MAX_KEYS = 10000


def client_ip():
    # Detrás del proxy de Render la IP real es la primera de X-Forwarded-For.
    forwarded = request.headers.get('X-Forwarded-For', '')
    return (forwarded.split(',')[0].strip() or request.remote_addr or 'unknown')


def _enabled():
    flag = current_app.config.get('RATE_LIMIT_ENABLED')
    return (not current_app.config.get('TESTING')) if flag is None else bool(flag)


def reset():
    with _lock:
        _hits.clear()


def rate_limit(limit, per_seconds=60, scope=None):
    """Máximo `limit` pedidos cada `per_seconds` por IP (y por `scope`, por defecto el endpoint)."""
    def decorator(f):
        name = scope or f.__name__

        @wraps(f)
        def wrapper(*args, **kwargs):
            if not _enabled():
                return f(*args, **kwargs)
            now = time.monotonic()
            key = (name, client_ip())
            with _lock:
                if len(_hits) > _MAX_KEYS:
                    for k in [k for k, q in _hits.items() if not q or now - q[-1] > per_seconds]:
                        del _hits[k]
                q = _hits.setdefault(key, deque())
                while q and now - q[0] > per_seconds:
                    q.popleft()
                if len(q) >= limit:
                    retry = max(1, int(per_seconds - (now - q[0])))
                    resp = jsonify({'error': 'Demasiados pedidos, probá de nuevo en un momento'})
                    resp.status_code = 429
                    resp.headers['Retry-After'] = str(retry)
                    return resp
                q.append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator
