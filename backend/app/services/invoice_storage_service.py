import os
import hashlib
from datetime import datetime
from typing import Tuple, Optional
import logging
from app.models.email_invoice import InvoiceAttachment
from app.extensions import db

logger = logging.getLogger(__name__)


class InvoiceStorageService:
    
    @staticmethod
    def get_storage_path() -> str:
        """Get the base storage path for invoice PDFs"""
        base_path = os.getenv('INVOICE_STORAGE_PATH', 'invoice_attachments')
        
        if not os.path.isabs(base_path):
            base_path = os.path.join(os.getcwd(), base_path)
        
        os.makedirs(base_path, exist_ok=True)
        return base_path
    
    @staticmethod
    def calculate_file_hash(content: bytes) -> str:
        """Calculate MD5 hash of file content"""
        return hashlib.md5(content).hexdigest()
    
    @staticmethod
    def check_duplicate_by_hash(file_hash: str) -> Optional[InvoiceAttachment]:
        """Check if a file with the same hash already exists"""
        return InvoiceAttachment.query.filter_by(file_hash=file_hash).first()
    
    @staticmethod
    def save_pdf_file(content: bytes, filename: str, email_invoice_id: int) -> Tuple[InvoiceAttachment, bool]:
        """
        Save PDF file to storage and create database record.
        Returns (InvoiceAttachment, is_duplicate)
        """
        file_hash = InvoiceStorageService.calculate_file_hash(content)
        
        # Check for duplicates
        existing = InvoiceStorageService.check_duplicate_by_hash(file_hash)
        if existing:
            logger.info(f"Duplicate file detected: {filename} (hash: {file_hash})")
            return existing, True
        
        # Generate storage path with date-based directory structure
        now = datetime.utcnow()
        year_month = now.strftime('%Y/%m')
        storage_dir = os.path.join(InvoiceStorageService.get_storage_path(), year_month)
        os.makedirs(storage_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        safe_filename = InvoiceStorageService._sanitize_filename(filename)
        unique_filename = f"{timestamp}_{safe_filename}"
        file_path = os.path.join(storage_dir, unique_filename)
        
        # Save file to disk
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
            logger.info(f"Saved PDF file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save PDF file: {str(e)}")
            raise
        
        # Create database record
        attachment = InvoiceAttachment(
            email_invoice_id=email_invoice_id,
            filename=filename,
            file_size=len(content),
            file_path=file_path,
            file_hash=file_hash
        )
        
        db.session.add(attachment)
        db.session.flush()
        
        return attachment, False
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Remove or replace unsafe characters from filename"""
        unsafe_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        safe_name = filename
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Limit length
        if len(safe_name) > 200:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:195] + ext
        
        return safe_name
