from datetime import datetime
from app.extensions import db

class LocationBoundary(db.Model):
    """
    Defines geofence boundaries for biometric check-in validation.
    Allows enforcement of location-based check-in (e.g., must be within café radius).
    """
    __tablename__ = 'location_boundaries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  # e.g., "Café Centro"
    latitude = db.Column(db.Float, nullable=False)  # Center point latitude
    longitude = db.Column(db.Float, nullable=False)  # Center point longitude
    radius_meters = db.Column(db.Float, nullable=False)  # Geofence radius
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<LocationBoundary {self.name} (radius: {self.radius_meters}m)>'

    def distance_from(self, latitude, longitude):
        """
        Calculate distance in meters between this boundary center and given coordinates.
        Uses Haversine formula for accurate great-circle distance.
        """
        from math import radians, cos, sin, asin, sqrt

        # Haversine formula
        lon1, lat1, lon2, lat2 = map(radians, [self.longitude, self.latitude, longitude, latitude])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371000  # Radius of earth in meters
        return c * r

    def is_within_boundary(self, latitude, longitude):
        """Check if given coordinates are within this geofence."""
        distance = self.distance_from(latitude, longitude)
        return distance <= self.radius_meters

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'radius_meters': self.radius_meters,
            'is_active': self.is_active,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
