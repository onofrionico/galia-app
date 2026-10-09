import logging

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.site_config import SiteConfig
from app.services.menu_image_service import MAX_UPLOAD_BYTES, InvalidImageError, process_image
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required
from app.utils.menu_storage import get_menu_storage, public_url

logger = logging.getLogger(__name__)

config_bp = Blueprint('config', __name__, url_prefix='/api/v1')

UPLOAD_OVERHEAD_BYTES = 1024 * 1024  # overhead multipart
# campo del formulario -> (atributo de SiteConfig, prefijo de clave, lado máximo)
BRANDING_FIELDS = {
    'logo': ('logo_path', 'branding/logo-', 800),
    'background': ('banner_background_path', 'branding/banner-', 1920),
}


@config_bp.route('/config/branding', methods=['GET'])
def get_branding_config():
    """Configuración de branding (pública: la usa la pantalla de login)."""
    config = SiteConfig.query.order_by(SiteConfig.id).first()
    if not config:
        return jsonify({'logo_path': None, 'banner_background_path': None}), 200
    return jsonify(config.to_dict()), 200


@config_bp.route('/admin/config/branding', methods=['POST'])
@token_required
@admin_required
def post_branding_config(current_user):
    """Sube logo y/o fondo del banner al prefijo público `branding/`."""
    if request.content_length is not None and request.content_length > 2 * MAX_UPLOAD_BYTES + UPLOAD_OVERHEAD_BYTES:
        return jsonify({'error': 'Las imágenes superan los 10 MB'}), 413
    uploads = {field: request.files.get(field) for field in BRANDING_FIELDS}
    uploads = {field: f for field, f in uploads.items() if f is not None and f.filename}
    if not uploads:
        return jsonify({'error': 'Enviá al menos un archivo (logo o background)'}), 400

    processed = {}
    for field, upload in uploads.items():
        attribute, prefix, max_side = BRANDING_FIELDS[field]
        try:
            processed[attribute] = process_image(upload.read(MAX_UPLOAD_BYTES + 1), max_side=max_side, key_prefix=prefix)
        except InvalidImageError as exc:
            return jsonify({'error': str(exc)}), 400

    storage = get_menu_storage()
    try:
        for body, key in processed.values():
            storage.put(key, body, 'image/webp', 'public, max-age=31536000, immutable')
    except Exception:
        logger.exception('Error subiendo imágenes de branding')
        return jsonify({'error': 'No se pudo subir la imagen, probá de nuevo'}), 502

    config = SiteConfig.query.order_by(SiteConfig.id).first()
    if not config:
        config = SiteConfig()
        db.session.add(config)
    for attribute, (_body, key) in processed.items():
        setattr(config, attribute, public_url(key))
    db.session.commit()
    return jsonify(config.to_dict()), 200
