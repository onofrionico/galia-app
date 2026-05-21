from datetime import datetime
from app.extensions import db

class WorkBlock(db.Model):
    __tablename__ = 'work_blocks'

    id = db.Column(db.Integer, primary_key=True)
    time_tracking_id = db.Column(db.Integer, db.ForeignKey('time_tracking.id'), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    # Biometric check-in fields
    latitude = db.Column(db.Float, nullable=True)  # GPS latitude from check-in
    longitude = db.Column(db.Float, nullable=True)  # GPS longitude from check-in
    accuracy = db.Column(db.Float, nullable=True)  # GPS accuracy in meters
    photo_url = db.Column(db.String(500), nullable=True)  # S3 URL to check-in photo
    biometric_confidence = db.Column(db.Float, nullable=True)  # Face recognition confidence (0-1)
    biometric_verified = db.Column(db.Boolean, default=False, nullable=False)  # Was face matched?
    entry_type = db.Column(db.String(50), default='legacy', nullable=False)  # 'qr_biometric', 'manual', 'legacy'
    raw_metadata = db.Column(db.JSON, nullable=True)  # Browser/device info, timestamps, etc.

    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    time_tracking = db.relationship('TimeTracking', backref='work_blocks')

    def to_dict(self, include_biometric=False):
        data = {
            'id': self.id,
            'start_time': self.start_time.strftime('%H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M:%S') if self.end_time else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'entry_type': self.entry_type,
        }

        if include_biometric:
            data.update({
                'latitude': self.latitude,
                'longitude': self.longitude,
                'accuracy': self.accuracy,
                'photo_url': self.photo_url,
                'biometric_confidence': self.biometric_confidence,
                'biometric_verified': self.biometric_verified,
                'raw_metadata': self.raw_metadata,
            })

        return data
