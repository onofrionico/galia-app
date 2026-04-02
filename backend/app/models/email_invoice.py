from app.extensions import db
from datetime import datetime


class EmailConfiguration(db.Model):
    __tablename__ = 'email_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String(255), nullable=False)
    imap_server = db.Column(db.String(255), nullable=False)
    imap_port = db.Column(db.Integer, nullable=False, default=993)
    username = db.Column(db.String(255), nullable=False)
    encrypted_password = db.Column(db.Text, nullable=False)
    use_ssl = db.Column(db.Boolean, default=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'email_address': self.email_address,
            'imap_server': self.imap_server,
            'imap_port': self.imap_port,
            'username': self.username,
            'use_ssl': self.use_ssl,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_sensitive:
            data['encrypted_password'] = self.encrypted_password
        return data


class EmailInvoice(db.Model):
    __tablename__ = 'email_invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(255), unique=True, nullable=False)
    subject = db.Column(db.String(500))
    sender = db.Column(db.String(255))
    received_date = db.Column(db.DateTime)
    processing_status = db.Column(db.String(50))
    processed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    attachments = db.relationship('InvoiceAttachment', backref='email_invoice', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'email_id': self.email_id,
            'subject': self.subject,
            'sender': self.sender,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'processing_status': self.processing_status,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class InvoiceAttachment(db.Model):
    __tablename__ = 'invoice_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    email_invoice_id = db.Column(db.Integer, db.ForeignKey('email_invoices.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_hash = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    expenses = db.relationship('Expense', backref='invoice_attachment', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email_invoice_id': self.email_invoice_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
