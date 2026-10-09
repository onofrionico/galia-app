import logging
import re

from flask import Blueprint, Response, jsonify

from app.services import menu_publish_service
from app.utils.menu_storage import get_menu_storage

# Endpoints públicos (sin auth) que consume la carta pública: /api/public/menu.json
# y /api/public/menu/images/<hash>.webp.
bp = Blueprint('public_menu', __name__, url_prefix='/api/public')
logger = logging.getLogger(__name__)

IMAGE_NAME = re.compile(r'^[0-9a-f]{16}\.webp$')


@bp.after_request
def allow_any_origin(response):
    # Recursos públicos de sólo lectura, sin credenciales: accesibles desde cualquier origen.
    if 'Access-Control-Allow-Origin' not in response.headers:
        response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@bp.route('/menu.json', methods=['GET'])
def menu_json():
    snapshot = menu_publish_service.published_snapshot()
    if snapshot is None:
        return jsonify({'error': 'La carta todavía no se publicó'}), 404
    return Response(snapshot, status=200, headers={
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'public, max-age=60',
    })


@bp.route('/menu/images/<name>', methods=['GET'])
def menu_image(name):
    if not IMAGE_NAME.fullmatch(name):
        return jsonify({'error': 'Imagen no encontrada'}), 404
    try:
        body, _ = get_menu_storage().get(f'images/{name}')
    except KeyError:
        return jsonify({'error': 'Imagen no encontrada'}), 404
    except Exception:
        logger.exception('No se pudo leer la imagen de la carta %s', name)
        return jsonify({'error': 'No se pudo obtener la imagen'}), 502
    return Response(body, status=200, headers={
        'Content-Type': 'image/webp',
        'Cache-Control': 'public, max-age=31536000, immutable',
    })
