import hashlib
import logging
import re
import threading
import time

from flask import Blueprint, Response, current_app, jsonify, request

from app.services import menu_publish_service
from app.utils.menu_storage import get_menu_storage
from app.utils.rate_limit import rate_limit

# Endpoints públicos (sin auth) que consume la carta pública: /api/public/menu.json
# y /api/public/menu/images/<hash>.webp.
bp = Blueprint('public_menu', __name__, url_prefix='/api/public')
logger = logging.getLogger(__name__)

IMAGE_NAME = re.compile(r'^[0-9a-f]{16}\.webp$')
# Imágenes de productos y branding: viven en el mismo storage, fuera de `images/`
# (que el publish de la carta limpia). Sus URLs las arma `public_url`.
ASSET_NAMES = {
    'products': IMAGE_NAME,
    'branding': re.compile(r'^(logo|banner)-[0-9a-f]{16}\.webp$'),
}


def _etag_core(value):
    """ETag sin W/, comillas ni sufijo ':gzip' (flask-compress reescribe el ETag de lo que comprime)."""
    value = value.strip()
    if value.startswith('W/'):
        value = value[2:]
    return value.strip('"').split(':', 1)[0]


def _not_modified(etag):
    """True si If-None-Match (puede traer varios valores, o '*') coincide con `etag`."""
    header = request.headers.get('If-None-Match', '')
    if not header:
        return False
    if header.strip() == '*':
        return True
    wanted = _etag_core(etag)
    return any(_etag_core(v) == wanted for v in header.split(','))


@bp.after_request
def allow_any_origin(response):
    # Recursos públicos de sólo lectura, sin credenciales: accesibles desde cualquier origen.
    if 'Access-Control-Allow-Origin' not in response.headers:
        response.headers['Access-Control-Allow-Origin'] = '*'
    return response


SNAPSHOT_TTL = 30  # segundos que el snapshot se sirve desde memoria sin releer la base
_snapshot_cache = {'at': 0.0, 'body': None, 'etag': None}
_snapshot_lock = threading.Lock()


def _cached_snapshot():
    use_cache = not current_app.config.get('TESTING')
    with _snapshot_lock:
        if use_cache and _snapshot_cache['body'] is not None and time.monotonic() - _snapshot_cache['at'] < SNAPSHOT_TTL:
            return _snapshot_cache['body'], _snapshot_cache['etag']
    snapshot = menu_publish_service.published_snapshot()
    if snapshot is None:
        return None, None
    raw = snapshot if isinstance(snapshot, bytes) else str(snapshot).encode('utf-8')
    etag = '"' + hashlib.sha1(raw).hexdigest()[:20] + '"'
    with _snapshot_lock:
        _snapshot_cache.update(at=time.monotonic(), body=snapshot, etag=etag)
    return snapshot, etag


@bp.route('/menu.json', methods=['GET'])
@rate_limit(120)
def menu_json():
    snapshot, etag = _cached_snapshot()
    if snapshot is None:
        return jsonify({'error': 'La carta todavía no se publicó'}), 404
    headers = {'Cache-Control': 'public, max-age=60', 'ETag': etag}
    if _not_modified(etag):
        return Response(status=304, headers=headers)
    headers['Content-Type'] = 'application/json; charset=utf-8'
    return Response(snapshot, status=200, headers=headers)


@bp.route('/menu/images/<name>', methods=['GET'])
@rate_limit(600, scope='menu_asset')
def menu_image(name):
    if not IMAGE_NAME.fullmatch(name):
        return jsonify({'error': 'Imagen no encontrada'}), 404
    return _serve_webp(f'images/{name}')


@bp.route('/menu/<folder>/<name>', methods=['GET'])
@rate_limit(600, scope='menu_asset')
def menu_asset(folder, name):
    pattern = ASSET_NAMES.get(folder)
    if pattern is None or not pattern.fullmatch(name):
        return jsonify({'error': 'Imagen no encontrada'}), 404
    return _serve_webp(f'{folder}/{name}')


def _serve_webp(key):
    # El nombre lleva el hash del contenido: nunca cambia, así que un pedido condicional no toca el storage.
    etag = '"' + key.rsplit('/', 1)[-1].rsplit('.', 1)[0] + '"'
    if _not_modified(etag):
        return Response(status=304, headers={'ETag': etag, 'Cache-Control': 'public, max-age=31536000, immutable'})
    try:
        body, _ = get_menu_storage().get(key)
    except KeyError:
        return jsonify({'error': 'Imagen no encontrada'}), 404
    except Exception:
        logger.exception('No se pudo leer la imagen %s', key)
        return jsonify({'error': 'No se pudo obtener la imagen'}), 502
    return Response(body, status=200, headers={
        'Content-Type': 'image/webp',
        'ETag': etag,
        'Cache-Control': 'public, max-age=31536000, immutable',
    })
