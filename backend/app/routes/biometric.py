from flask import Blueprint, request, jsonify
import qrcode
from io import BytesIO
import base64
import secrets
import logging
from datetime import datetime, timedelta, date, time
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.employee import Employee
from app.models.biometric_session import BiometricSession
from app.models.location_boundary import LocationBoundary
from app.models.time_tracking import TimeTracking
from app.models.work_block import WorkBlock
from app.utils.jwt_utils import token_required
from app.utils.timezone_utils import get_current_time_argentina, get_current_time_only_argentina, get_current_date_argentina
from app.utils.s3_utils import upload_to_s3

logger = logging.getLogger(__name__)
bp = Blueprint('biometric', __name__, url_prefix='/api/v1/biometric')

# Configuration
QR_TOKEN_EXPIRY_MINUTES = 5
QR_CODE_SIZE = 10  # QR code box size in pixels
BIOMETRIC_CONFIDENCE_THRESHOLD = 0.85  # Confidence threshold for face recognition
GPS_ACCURACY_THRESHOLD_METERS = 100  # GPS accuracy threshold

def generate_session_token():
    """Generate a secure random token for QR code."""
    return secrets.token_urlsafe(32)

def generate_qr_code(token, employee_id):
    """
    Generate a QR code that encodes the session token and employee ID.
    Returns base64-encoded PNG image.
    """
    try:
        # QR payload: token and employee_id in a simple format
        qr_payload = f"biometric://{employee_id}/{token}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=QR_CODE_SIZE,
            border=2,
        )
        qr.add_data(qr_payload)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert PIL image to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        buffered.seek(0)
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        raise


@bp.route('/qr-generate', methods=['POST'])
@token_required
def generate_qr(current_user):
    """
    Generate a QR code session for the current employee.
    QR code is valid for QR_TOKEN_EXPIRY_MINUTES minutes.
    """
    try:
        if not current_user.employee:
            return jsonify({'error': 'Usuario no es un empleado'}), 403

        employee = current_user.employee

        # Generate session token
        session_token = generate_session_token()

        # Create BiometricSession record
        expires_at = datetime.utcnow() + timedelta(minutes=QR_TOKEN_EXPIRY_MINUTES)

        biometric_session = BiometricSession(
            employee_id=employee.id,
            session_token=session_token,
            qr_generated_at=datetime.utcnow(),
            expires_at=expires_at,
            status='active'
        )

        db.session.add(biometric_session)
        db.session.commit()

        # Generate QR code
        qr_code_data = generate_qr_code(session_token, employee.id)

        return jsonify({
            'success': True,
            'qr_code': qr_code_data,
            'token': session_token,
            'employee_id': employee.id,
            'employee_name': f"{employee.first_name} {employee.last_name}",
            'expires_at': expires_at.isoformat(),
            'message': 'Por favor permite acceso a cámara y GPS'
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating QR: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/qr/<token>', methods=['GET'])
def validate_qr(token):
    """
    Validate and retrieve QR session information.
    This endpoint is called when the QR is scanned (no auth required).
    """
    try:
        biometric_session = BiometricSession.query.filter_by(
            session_token=token
        ).first()

        if not biometric_session:
            return jsonify({'error': 'QR inválido o no existe'}), 404

        # Check if expired
        if biometric_session.is_expired():
            biometric_session.status = 'expired'
            db.session.commit()
            return jsonify({'error': 'QR expirado'}), 410

        # Check if already used
        if biometric_session.status == 'used':
            return jsonify({'error': 'QR ya utilizado'}), 410

        # Mark as scanned
        biometric_session.mark_scanned()
        db.session.commit()

        employee = biometric_session.employee

        return jsonify({
            'valid': True,
            'employee_id': employee.id,
            'employee_name': f"{employee.first_name} {employee.last_name}",
            'session_token': token,
            'message': 'Identidad verificada. Permite acceso a cámara y GPS',
        }), 200

    except Exception as e:
        logger.error(f"Error validating QR: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error validando QR'}), 500


@bp.route('/check-in', methods=['POST'])
def check_in_biometric():
    """
    Register a biometric check-in with QR token, photo, GPS, and biometric verification.
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['qr_token', 'entry_type', 'photo_base64', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({'error': f'Campo requerido faltante: {field}'}), 400

        qr_token = data.get('qr_token')
        entry_type = data.get('entry_type')  # 'in' or 'out'
        photo_base64 = data.get('photo_base64')
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        accuracy = float(data.get('accuracy', 0))
        biometric_confidence = float(data.get('biometric_confidence', 0))
        biometric_verified = bool(data.get('biometric_verified', False))

        # Validate entry_type
        if entry_type not in ['in', 'out']:
            return jsonify({'error': 'entry_type debe ser "in" o "out"'}), 400

        # Validate biometric confidence threshold
        if not biometric_verified or biometric_confidence < BIOMETRIC_CONFIDENCE_THRESHOLD:
            return jsonify({
                'error': 'Biometría no verificada',
                'confidence': biometric_confidence,
                'threshold': BIOMETRIC_CONFIDENCE_THRESHOLD
            }), 403

        # Validate GPS accuracy
        if accuracy > GPS_ACCURACY_THRESHOLD_METERS:
            logger.warning(f"GPS accuracy degraded: {accuracy}m (threshold: {GPS_ACCURACY_THRESHOLD_METERS}m)")
            # Still allow, but log warning

        # Validate QR session
        biometric_session = BiometricSession.query.filter_by(
            session_token=qr_token
        ).first()

        if not biometric_session:
            return jsonify({'error': 'Sesión QR inválida'}), 404

        if biometric_session.is_expired() or biometric_session.status != 'active':
            return jsonify({'error': 'Sesión QR expirada o inválida'}), 410

        employee = biometric_session.employee

        # Validate location (geofencing - optional)
        if biometric_session.qr_location_id:
            location = LocationBoundary.query.filter_by(
                id=biometric_session.qr_location_id,
                is_active=True
            ).first()

            if location:
                if not location.is_within_boundary(latitude, longitude):
                    distance = location.distance_from(latitude, longitude)
                    return jsonify({
                        'error': f'Ubicación fuera del área permitida',
                        'distance_meters': round(distance, 2),
                        'boundary_radius': location.radius_meters
                    }), 403

        # Get today's tracking record (or create new one)
        tracking_date = get_current_date_argentina()
        tracking = TimeTracking.query.filter_by(
            employee_id=employee.id,
            tracking_date=tracking_date
        ).first()

        if not tracking:
            tracking = TimeTracking(
                employee_id=employee.id,
                tracking_date=tracking_date
            )
            db.session.add(tracking)
            db.session.flush()

        current_time = get_current_time_only_argentina()

        # Upload photo to S3
        photo_url = None
        if photo_base64:
            try:
                photo_url = upload_to_s3(
                    photo_base64,
                    f"biometric/{employee.id}/{datetime.utcnow().timestamp()}.jpg",
                    content_type='image/jpeg'
                )
            except Exception as e:
                logger.error(f"Error uploading photo to S3: {str(e)}")
                # Don't fail the entire request if photo upload fails
                photo_url = None

        # Create or update WorkBlock
        if entry_type == 'in':
            # Check for active block
            for block in tracking.work_blocks:
                if block.end_time == block.start_time:  # Active block
                    return jsonify({
                        'error': 'Ya existe una entrada activa. Registra la salida primero.'
                    }), 409

            # Create new work block
            work_block = WorkBlock(
                time_tracking_id=tracking.id,
                start_time=current_time,
                end_time=current_time,  # Will be updated on check-out
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                photo_url=photo_url,
                biometric_confidence=biometric_confidence,
                biometric_verified=biometric_verified,
                entry_type='qr_biometric',
                raw_metadata={
                    'gps_accuracy': accuracy,
                    'biometric_confidence': biometric_confidence,
                    'browser': data.get('browser_info'),
                }
            )
            db.session.add(work_block)
            db.session.flush()

            # Mark session as used
            biometric_session.mark_used(work_block.id)

            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Entrada registrada',
                'work_block_id': work_block.id,
                'timestamp': current_time.isoformat(),
                'entry_type': 'in'
            }), 201

        else:  # entry_type == 'out'
            # Find last active block
            active_block = None
            for block in tracking.work_blocks:
                if block.end_time == block.start_time:  # Active block
                    active_block = block
                    break

            if not active_block:
                return jsonify({
                    'error': 'No hay entrada activa para registrar salida'
                }), 409

            # Update end_time
            active_block.end_time = current_time
            active_block.latitude = latitude
            active_block.longitude = longitude
            active_block.accuracy = accuracy
            if photo_url:  # Update photo if provided
                active_block.photo_url = photo_url
            active_block.biometric_confidence = biometric_confidence
            active_block.biometric_verified = biometric_verified
            if active_block.entry_type == 'legacy':  # Only update if was legacy
                active_block.entry_type = 'qr_biometric'

            # Mark session as used
            biometric_session.mark_used(active_block.id)

            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Salida registrada',
                'work_block_id': active_block.id,
                'timestamp': current_time.isoformat(),
                'entry_type': 'out'
            }), 200

    except ValueError as e:
        logger.error(f"Valor inválido en biometric check-in: {str(e)}")
        return jsonify({'error': f'Dato inválido: {str(e)}'}), 400
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError en biometric check-in: {str(e)}")
        return jsonify({'error': 'Error al registrar entrada'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error en biometric check-in: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/verify-face', methods=['POST'])
def verify_face():
    """
    Verify facial recognition by comparing current photo with employee profile photo.
    This is optional and can use multiple strategies (local ML, AWS Rekognition, etc).
    """
    try:
        data = request.get_json()

        photo_base64 = data.get('photo_base64')
        stored_photo_url = data.get('stored_photo_url')

        if not photo_base64:
            return jsonify({'error': 'Photo required'}), 400

        # For MVP: Just return a mock confidence score
        # In production, integrate with:
        # - face_recognition library for local comparison
        # - AWS Rekognition for cloud-based comparison
        # - Deepface for more advanced options

        # Mock response
        confidence = 0.92
        verified = confidence >= BIOMETRIC_CONFIDENCE_THRESHOLD

        return jsonify({
            'verified': verified,
            'confidence': confidence,
            'threshold': BIOMETRIC_CONFIDENCE_THRESHOLD
        }), 200

    except Exception as e:
        logger.error(f"Error in face verification: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error verifying face'}), 500
