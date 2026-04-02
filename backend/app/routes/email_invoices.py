from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.email_invoice import EmailConfiguration, EmailInvoice
from app.models.expense import Expense
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required
from app.services.email_service import EmailService
from app.services.invoice_processor import InvoiceProcessor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('email_invoices', __name__, url_prefix='/api/v1/email-invoices')


@bp.route('/config', methods=['GET'])
@token_required
@admin_required
def get_email_config(current_user):
    """Get email configuration"""
    config = EmailConfiguration.query.filter_by(is_active=True).first()
    if not config:
        return jsonify({'message': 'No email configuration found'}), 404
    
    return jsonify(config.to_dict(include_sensitive=False)), 200


@bp.route('/config', methods=['POST'])
@token_required
@admin_required
def create_email_config(current_user):
    """Create or update email configuration"""
    data = request.get_json()
    
    required_fields = ['email_address', 'imap_server', 'imap_port', 'username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Deactivate existing configs
    EmailConfiguration.query.update({'is_active': False})
    
    # Encrypt password
    encrypted_password = EmailService.encrypt_password(data['password'])
    
    config = EmailConfiguration(
        email_address=data['email_address'],
        imap_server=data['imap_server'],
        imap_port=data['imap_port'],
        username=data['username'],
        encrypted_password=encrypted_password,
        use_ssl=data.get('use_ssl', True),
        is_active=True
    )
    
    db.session.add(config)
    db.session.commit()
    
    return jsonify(config.to_dict(include_sensitive=False)), 201


@bp.route('/config/test', methods=['POST'])
@token_required
@admin_required
def test_email_connection(current_user):
    """Test email connection with provided credentials"""
    data = request.get_json()
    
    required_fields = ['imap_server', 'imap_port', 'username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Create temporary config for testing
    encrypted_password = EmailService.encrypt_password(data['password'])
    temp_config = EmailConfiguration(
        email_address=data.get('email_address', data['username']),
        imap_server=data['imap_server'],
        imap_port=data['imap_port'],
        username=data['username'],
        encrypted_password=encrypted_password,
        use_ssl=data.get('use_ssl', True)
    )
    
    success, error_message = EmailService.test_connection(temp_config)
    
    if success:
        return jsonify({'success': True, 'message': 'Connection successful'}), 200
    else:
        return jsonify({'success': False, 'error': error_message}), 400


@bp.route('/process', methods=['POST'])
@token_required
@admin_required
def trigger_processing(current_user):
    """Manually trigger email processing"""
    try:
        # Process immediately (synchronous for now, can be made async with Celery later)
        results = InvoiceProcessor.process_pending_invoices()
        
        return jsonify({
            'status': 'completed',
            'message': 'Processing completed',
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error in trigger_processing: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/history', methods=['GET'])
@token_required
@admin_required
def get_processing_history(current_user):
    """Get history of processed emails"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = EmailInvoice.query.order_by(EmailInvoice.created_at.desc())
    
    total = query.count()
    emails = query.paginate(page=page, per_page=per_page, error_out=False)
    
    items = []
    for email in emails.items:
        email_dict = email.to_dict()
        
        # Add expense info if exists
        if email.attachments:
            attachment = email.attachments[0]
            if attachment.expenses:
                expense = attachment.expenses[0]
                email_dict['expense_id'] = expense.id
                email_dict['expense_importe'] = float(expense.importe) if expense.importe else 0
        
        items.append(email_dict)
    
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': emails.pages,
        'items': items
    }), 200


@bp.route('/stats', methods=['GET'])
@token_required
@admin_required
def get_stats(current_user):
    """Get statistics about email invoice processing"""
    from sqlalchemy import func
    
    total_emails = EmailInvoice.query.count()
    success_emails = EmailInvoice.query.filter_by(processing_status='success').count()
    error_emails = EmailInvoice.query.filter_by(processing_status='error').count()
    duplicate_emails = EmailInvoice.query.filter_by(processing_status='duplicate').count()
    
    total_auto_expenses = Expense.query.filter_by(source='email_auto').count()
    
    return jsonify({
        'emails': {
            'total': total_emails,
            'success': success_emails,
            'error': error_emails,
            'duplicate': duplicate_emails
        },
        'expenses': {
            'total': total_auto_expenses
        }
    }), 200
