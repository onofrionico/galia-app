from datetime import datetime, timedelta
from app.extensions import db

class BiometricSession(db.Model):
    """
    Tracks QR code sessions for biometric check-in.
    Each session has a unique token, expiry time, and lifecycle status.
    """
    __tablename__ = 'biometric_sessions'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    qr_location_id = db.Column(db.String(100), nullable=True)  # Salon/location binding
    qr_generated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    qr_scanned_at = db.Column(db.DateTime, nullable=True)  # When QR was first scanned
    status = db.Column(
        db.String(20),
        default='active',
        nullable=False,
        index=True
    )  # 'active', 'used', 'expired'
    expires_at = db.Column(db.DateTime, nullable=False, index=True)  # QR expiry time
    work_block_id = db.Column(db.Integer, db.ForeignKey('work_blocks.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    employee = db.relationship('Employee', backref='biometric_sessions')
    work_block = db.relationship('WorkBlock', backref='biometric_session')

    def __repr__(self):
        return f'<BiometricSession {self.session_token[:10]}... ({self.status})>'

    def is_expired(self):
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at

    def is_valid(self):
        """Check if session is valid (active and not expired)."""
        return self.status == 'active' and not self.is_expired()

    def mark_scanned(self):
        """Mark the session as scanned."""
        self.qr_scanned_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_used(self, work_block_id=None):
        """Mark the session as used (successfully completed check-in)."""
        self.status = 'used'
        self.work_block_id = work_block_id
        self.updated_at = datetime.utcnow()

    def mark_expired(self):
        """Mark the session as expired."""
        self.status = 'expired'
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'session_token': self.session_token,
            'qr_location_id': self.qr_location_id,
            'qr_generated_at': self.qr_generated_at.isoformat() if self.qr_generated_at else None,
            'qr_scanned_at': self.qr_scanned_at.isoformat() if self.qr_scanned_at else None,
            'status': self.status,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'work_block_id': self.work_block_id,
            'is_valid': self.is_valid(),
        }
