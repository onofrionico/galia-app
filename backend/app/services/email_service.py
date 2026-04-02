import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime
from typing import List, Dict, Optional
import logging
from cryptography.fernet import Fernet
from app.models.email_invoice import EmailConfiguration

logger = logging.getLogger(__name__)


class EmailService:
    
    PENDING_LABEL = "Facturas pendientes"
    PROCESSED_LABEL = "Factura procesada"
    
    @staticmethod
    def encrypt_password(password: str) -> str:
        """Encrypt password using Fernet"""
        key = os.getenv('EMAIL_ENCRYPTION_KEY')
        if not key:
            raise ValueError("EMAIL_ENCRYPTION_KEY not set in environment")
        
        f = Fernet(key.encode())
        encrypted = f.encrypt(password.encode())
        return encrypted.decode()
    
    @staticmethod
    def decrypt_password(encrypted_password: str) -> str:
        """Decrypt password using Fernet"""
        key = os.getenv('EMAIL_ENCRYPTION_KEY')
        if not key:
            raise ValueError("EMAIL_ENCRYPTION_KEY not set in environment")
        
        f = Fernet(key.encode())
        decrypted = f.decrypt(encrypted_password.encode())
        return decrypted.decode()
    
    @staticmethod
    def connect_to_mailbox(config: EmailConfiguration):
        """Connect to IMAP mailbox"""
        try:
            password = EmailService.decrypt_password(config.encrypted_password)
            
            if config.use_ssl:
                mail = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
            else:
                mail = imaplib.IMAP4(config.imap_server, config.imap_port)
            
            mail.login(config.username, password)
            logger.info(f"Connected to {config.imap_server} as {config.username}")
            return mail
            
        except Exception as e:
            logger.error(f"Failed to connect to mailbox: {str(e)}")
            raise
    
    @staticmethod
    def test_connection(config: EmailConfiguration) -> tuple[bool, Optional[str]]:
        """Test email connection"""
        try:
            mail = EmailService.connect_to_mailbox(config)
            mail.logout()
            return True, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_gmail_label_id(mail, label_name: str) -> Optional[str]:
        """Get Gmail label ID by name"""
        try:
            # List all labels
            status, labels = mail.list()
            if status != 'OK':
                return None
            
            for label in labels:
                label_str = label.decode()
                if label_name in label_str:
                    return label_name
            
            return None
        except Exception as e:
            logger.error(f"Error getting label ID: {str(e)}")
            return None
    
    @staticmethod
    def fetch_emails_with_label(config: EmailConfiguration, label: str) -> List[Dict]:
        """Fetch emails with specific Gmail label"""
        try:
            mail = EmailService.connect_to_mailbox(config)
            
            # Select INBOX
            mail.select('INBOX')
            
            # Search for emails with the label
            # Gmail uses X-GM-LABELS for label search
            search_criteria = f'X-GM-LABELS "{label}"'
            
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK':
                logger.warning(f"No messages found with label: {label}")
                return []
            
            email_ids = messages[0].split()
            logger.info(f"Found {len(email_ids)} emails with label '{label}'")
            
            emails = []
            for email_id in email_ids:
                email_data = EmailService._fetch_email_by_id(mail, email_id)
                if email_data:
                    emails.append(email_data)
            
            mail.logout()
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            raise
    
    @staticmethod
    def _fetch_email_by_id(mail, email_id) -> Optional[Dict]:
        """Fetch single email by ID"""
        try:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            
            if status != 'OK':
                return None
            
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Decode subject
            subject = EmailService._decode_header(email_message['Subject'])
            sender = EmailService._decode_header(email_message['From'])
            date_str = email_message['Date']
            
            # Parse date
            received_date = None
            if date_str:
                try:
                    received_date = email.utils.parsedate_to_datetime(date_str)
                except:
                    received_date = datetime.utcnow()
            
            # Extract attachments
            attachments = EmailService._extract_attachments(email_message)
            
            return {
                'email_id': email_id.decode(),
                'subject': subject,
                'sender': sender,
                'received_date': received_date,
                'attachments': attachments
            }
            
        except Exception as e:
            logger.error(f"Error fetching email {email_id}: {str(e)}")
            return None
    
    @staticmethod
    def _decode_header(header_value):
        """Decode email header"""
        if not header_value:
            return ""
        
        decoded_parts = decode_header(header_value)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_string += part
        
        return decoded_string
    
    @staticmethod
    def _extract_attachments(email_message) -> List[Dict]:
        """Extract PDF attachments from email"""
        attachments = []
        
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            
            if part.get('Content-Disposition') is None:
                continue
            
            filename = part.get_filename()
            if not filename:
                continue
            
            # Only process PDF files
            if not filename.lower().endswith('.pdf'):
                continue
            
            content = part.get_payload(decode=True)
            
            attachments.append({
                'filename': filename,
                'content': content,
                'size': len(content)
            })
        
        return attachments
    
    @staticmethod
    def change_email_label(config: EmailConfiguration, email_id: str, 
                          remove_label: str, add_label: str) -> bool:
        """Change email label (remove one, add another)"""
        try:
            mail = EmailService.connect_to_mailbox(config)
            mail.select('INBOX')
            
            # Gmail IMAP uses +X-GM-LABELS and -X-GM-LABELS
            # Remove old label
            if remove_label:
                mail.store(email_id.encode(), '-X-GM-LABELS', f'"{remove_label}"')
            
            # Add new label
            if add_label:
                mail.store(email_id.encode(), '+X-GM-LABELS', f'"{add_label}"')
            
            mail.logout()
            logger.info(f"Changed label for email {email_id}: -{remove_label} +{add_label}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing email label: {str(e)}")
            return False
    
    @staticmethod
    def mark_as_processed(config: EmailConfiguration, email_id: str) -> bool:
        """Mark email as processed (change label)"""
        return EmailService.change_email_label(
            config, 
            email_id, 
            EmailService.PENDING_LABEL,
            EmailService.PROCESSED_LABEL
        )
    
    @staticmethod
    def keep_as_pending(config: EmailConfiguration, email_id: str) -> bool:
        """Keep email as pending (no label change)"""
        # No action needed, email keeps its current label
        return True
