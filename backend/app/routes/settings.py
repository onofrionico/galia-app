from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models import AppSettings, User
from app.utils.jwt_utils import token_required
import os
import base64
from werkzeug.utils import secure_filename

settings_bp = Blueprint('settings', __name__, url_prefix='/api')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@settings_bp.route('/settings', methods=['GET'])
@token_required
def get_settings(current_user):
    settings = AppSettings.query.first()
    
    if not settings:
        settings = AppSettings()
        db.session.add(settings)
        db.session.commit()
    
    return jsonify(settings.to_dict()), 200

@settings_bp.route('/settings', methods=['PUT'])
@token_required
def update_settings(current_user):
    user = current_user
    
    if not user or user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.get_json()
    settings = AppSettings.query.first()
    
    if not settings:
        settings = AppSettings()
        db.session.add(settings)
    
    if 'primary_color' in data:
        settings.primary_color = data['primary_color']
    if 'secondary_color' in data:
        settings.secondary_color = data['secondary_color']
    if 'accent_color' in data:
        settings.accent_color = data['accent_color']
    if 'cafeteria_name' in data:
        settings.cafeteria_name = data['cafeteria_name']
    
    db.session.commit()
    
    return jsonify(settings.to_dict()), 200

@settings_bp.route('/settings/logo', methods=['POST'])
@token_required
def upload_logo(current_user):
    user = current_user
    
    if not user or user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    if 'logo' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo'}), 400
    
    file = request.files['logo']
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó archivo'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = int(os.path.getmtime(__file__) if os.path.exists(__file__) else 0)
        unique_filename = f"logo_{timestamp}_{filename}"
        
        upload_folder = os.path.join(current_app.root_path, '..', 'uploads', 'logos')
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        logo_url = f'/uploads/logos/{unique_filename}'
        
        settings = AppSettings.query.first()
        if not settings:
            settings = AppSettings()
            db.session.add(settings)
        
        settings.logo_url = logo_url
        db.session.commit()
        
        return jsonify({'logo_url': logo_url}), 200
    
    return jsonify({'error': 'Tipo de archivo no permitido'}), 400

@settings_bp.route('/settings/logo', methods=['DELETE'])
@token_required
def delete_logo(current_user):
    user = current_user
    
    if not user or user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    settings = AppSettings.query.first()
    
    if settings and settings.logo_url:
        try:
            filepath = os.path.join(current_app.root_path, '..', settings.logo_url.lstrip('/'))
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            current_app.logger.error(f"Error al eliminar logo: {str(e)}")
        
        settings.logo_url = None
        db.session.commit()
    
    return jsonify({'message': 'Logo eliminado'}), 200
