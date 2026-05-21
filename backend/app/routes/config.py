from flask import Blueprint, jsonify
from app.models.site_config import SiteConfig

config_bp = Blueprint('config', __name__, url_prefix='/api/v1/config')


@config_bp.route('/branding', methods=['GET'])
def get_branding_config():
    """Get current branding configuration (logo and banner background paths)"""
    config = SiteConfig.query.first()

    if not config:
        return jsonify({
            'logo_path': None,
            'banner_background_path': None
        }), 200

    return jsonify(config.to_dict()), 200
