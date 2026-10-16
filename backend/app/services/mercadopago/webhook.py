"""Verificación de la firma de los avisos de MercadoPago (header x-signature: ts=...,v1=...)."""
import hashlib
import hmac


def _parts(x_signature):
    parts = {}
    for chunk in (x_signature or '').split(','):
        key, _, value = chunk.strip().partition('=')
        if key and value:
            parts[key] = value
    return parts


def manifest(data_id, request_id, ts):
    """id:<data.id>;request-id:<x-request-id>;ts:<ts>; (las partes que faltan se omiten; id en minúsculas)."""
    text = ''
    if data_id:
        text += f'id:{str(data_id).lower()};'
    if request_id:
        text += f'request-id:{request_id};'
    if ts:
        text += f'ts:{ts};'
    return text


def verify_signature(secret, x_signature, x_request_id, data_id):
    parts = _parts(x_signature)
    if not secret or 'ts' not in parts or 'v1' not in parts:
        return False
    expected = hmac.new(secret.encode(), manifest(data_id, x_request_id, parts['ts']).encode(),
                        hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, parts['v1'])
