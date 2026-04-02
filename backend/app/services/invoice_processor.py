from datetime import datetime
from typing import Dict, List
import logging
from app.models.email_invoice import EmailConfiguration, EmailInvoice, InvoiceAttachment
from app.models.expense import Expense, ExpenseCategory
from app.extensions import db
from app.services.email_service import EmailService
from app.services.pdf_extraction_service import PDFExtractionService
from app.services.invoice_storage_service import InvoiceStorageService

logger = logging.getLogger(__name__)


class InvoiceProcessor:
    
    CONFIDENCE_THRESHOLD = 50  # Minimum confidence to create expense
    
    @staticmethod
    def process_pending_invoices(config_id: int = None) -> Dict:
        """
        Main processing function: fetch emails with pending label and process them
        """
        results = {
            'emails_found': 0,
            'emails_processed': 0,
            'emails_error': 0,
            'expenses_created': 0,
            'details': []
        }
        
        try:
            # Get active email configuration
            if config_id:
                config = EmailConfiguration.query.get(config_id)
            else:
                config = EmailConfiguration.query.filter_by(is_active=True).first()
            
            if not config:
                logger.error("No active email configuration found")
                return {
                    'error': 'No active email configuration found',
                    'emails_found': 0
                }
            
            # Fetch emails with "Facturas pendientes" label
            emails = EmailService.fetch_emails_with_label(config, EmailService.PENDING_LABEL)
            results['emails_found'] = len(emails)
            
            logger.info(f"Found {len(emails)} emails with label '{EmailService.PENDING_LABEL}'")
            
            # Process each email
            for email_data in emails:
                result = InvoiceProcessor._process_single_email(config, email_data)
                results['details'].append(result)
                
                if result['status'] == 'success':
                    results['emails_processed'] += 1
                    results['expenses_created'] += 1
                else:
                    results['emails_error'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error in process_pending_invoices: {str(e)}")
            return {
                'error': str(e),
                'emails_found': results['emails_found'],
                'emails_processed': results['emails_processed']
            }
    
    @staticmethod
    def _process_single_email(config: EmailConfiguration, email_data: Dict) -> Dict:
        """Process a single email"""
        result = {
            'email_id': email_data['email_id'],
            'subject': email_data['subject'],
            'status': 'error',
            'error': None,
            'expense_id': None
        }
        
        try:
            # Save email to database
            email_invoice = EmailInvoice(
                email_id=email_data['email_id'],
                subject=email_data['subject'],
                sender=email_data['sender'],
                received_date=email_data['received_date']
            )
            db.session.add(email_invoice)
            db.session.flush()
            
            # Check if email has PDF attachments
            if not email_data.get('attachments'):
                result['error'] = 'No PDF attachments found'
                result['status'] = 'error'
                email_invoice.processing_status = 'error'
                email_invoice.error_message = result['error']
                email_invoice.processed_at = datetime.utcnow()
                db.session.commit()
                return result
            
            # Process first PDF attachment
            attachment_data = email_data['attachments'][0]
            
            # Save PDF to storage
            attachment, is_duplicate = InvoiceStorageService.save_pdf_file(
                content=attachment_data['content'],
                filename=attachment_data['filename'],
                email_invoice_id=email_invoice.id
            )
            
            if is_duplicate:
                result['error'] = 'Duplicate PDF file (same hash)'
                result['status'] = 'duplicate'
                email_invoice.processing_status = 'duplicate'
                email_invoice.error_message = result['error']
                email_invoice.processed_at = datetime.utcnow()
                db.session.commit()
                return result
            
            # Extract invoice data from PDF
            extracted_data, raw_text, method = PDFExtractionService.extract_invoice_from_pdf(
                attachment_data['content']
            )
            
            # Check confidence score
            confidence = extracted_data.get('confidence', 0)
            if confidence < InvoiceProcessor.CONFIDENCE_THRESHOLD:
                result['error'] = f'Confidence score too low ({confidence}%)'
                result['status'] = 'error'
                email_invoice.processing_status = 'error'
                email_invoice.error_message = result['error']
                email_invoice.processed_at = datetime.utcnow()
                db.session.commit()
                return result
            
            # Check for duplicate invoice (by numero_comprobante + CUIT)
            if InvoiceProcessor._is_duplicate_invoice(extracted_data):
                result['error'] = 'Duplicate invoice (same numero_comprobante + CUIT)'
                result['status'] = 'duplicate'
                email_invoice.processing_status = 'duplicate'
                email_invoice.error_message = result['error']
                email_invoice.processed_at = datetime.utcnow()
                db.session.commit()
                return result
            
            # Create expense
            expense = InvoiceProcessor._create_expense_from_data(extracted_data, attachment.id)
            
            # Mark email as successfully processed
            email_invoice.processing_status = 'success'
            email_invoice.processed_at = datetime.utcnow()
            db.session.commit()
            
            # Change email label to "Factura procesada"
            EmailService.mark_as_processed(config, email_data['email_id'])
            
            result['status'] = 'success'
            result['expense_id'] = expense.id
            
            logger.info(f"Successfully processed email {email_data['email_id']}, created expense {expense.id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing email {email_data['email_id']}: {str(e)}")
            db.session.rollback()
            result['error'] = str(e)
            result['status'] = 'error'
            return result
    
    @staticmethod
    def _is_duplicate_invoice(extracted_data: Dict) -> bool:
        """Check if invoice already exists in database"""
        numero_comprobante = extracted_data.get('numero_comprobante')
        cuit = extracted_data.get('cuit')
        
        if not numero_comprobante or not cuit:
            return False
        
        existing = Expense.query.filter_by(
            numero_comprobante=numero_comprobante,
            numero_fiscal=cuit,
            cancelado=False
        ).first()
        
        return existing is not None
    
    @staticmethod
    def _create_expense_from_data(extracted_data: Dict, attachment_id: int) -> Expense:
        """Create Expense record from extracted data"""
        # Get or create default category
        default_category = ExpenseCategory.query.filter_by(name='Sin categoría').first()
        if not default_category:
            default_category = ExpenseCategory(
                name='Sin categoría',
                expense_type='indirecto',
                is_active=True
            )
            db.session.add(default_category)
            db.session.flush()
        
        expense = Expense(
            fecha=extracted_data.get('fecha_emision') or datetime.utcnow().date(),
            proveedor=extracted_data.get('proveedor'),
            numero_fiscal=extracted_data.get('cuit'),
            tipo_comprobante=extracted_data.get('tipo_comprobante'),
            numero_comprobante=extracted_data.get('numero_comprobante'),
            importe=extracted_data.get('importe_total') or 0,
            estado_pago='Pendiente',
            category_id=default_category.id,
            source='email_auto',
            invoice_attachment_id=attachment_id,
            creado_por='Sistema Automático',
            comentario=f"CAE: {extracted_data.get('cae')}" if extracted_data.get('cae') else None
        )
        
        db.session.add(expense)
        db.session.flush()
        
        return expense
