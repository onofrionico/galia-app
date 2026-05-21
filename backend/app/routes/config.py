from flask import Blueprint, jsonify, request
from app.models.site_config import SiteConfig
from app.extensions import db
from app.utils.file_upload import save_upload_file
from app.utils.jwt_utils import token_required

config_bp = Blueprint('config', __name__, url_prefix='/api/v1')


@config_bp.route('/config/branding', methods=['GET'])
def get_branding_config():
    """Get current branding configuration (logo and banner background paths)"""
    config = SiteConfig.query.first()

    if not config:
        return jsonify({
            'logo_path': None,
            'banner_background_path': None
        }), 200

    return jsonify(config.to_dict()), 200


@config_bp.route('/admin/config/branding', methods=['POST'])
@token_required
def post_branding_config(current_user):
    """Update branding configuration with logo and/or background image uploads (admin only)"""
    # Check admin permission
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    logo_file = request.files.get('logo')
    background_file = request.files.get('background')

    if not logo_file and not background_file:
        return jsonify({'error': 'At least one file must be provided'}), 400

    try:
        config = SiteConfig.query.first()
        if not config:
            config = SiteConfig()
            db.session.add(config)

        if logo_file and logo_file.filename != '':
            config.logo_path = save_upload_file(logo_file)

        if background_file and background_file.filename != '':
            config.banner_background_path = save_upload_file(background_file)

        db.session.commit()
        return jsonify(config.to_dict()), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update configuration'}), 500
