#!/usr/bin/env python3
"""
Seed biometric locations for testing geofencing features.
This creates location boundaries for checking in from specific places.
"""

from app import create_app, db
from app.models.location_boundary import LocationBoundary

def seed_locations():
    app = create_app('development')

    with app.app_context():
        # Clear existing locations
        LocationBoundary.query.delete()

        # Define test locations (Buenos Aires area for testing)
        locations = [
            {
                'name': 'Café Centro Principal',
                'latitude': -34.6037,  # Buenos Aires coordinates
                'longitude': -58.3816,
                'radius_meters': 50,
                'description': 'Sucursal principal en el centro',
            },
            {
                'name': 'Café Zona Norte',
                'latitude': -34.5895,
                'longitude': -58.3810,
                'radius_meters': 75,
                'description': 'Sucursal en zona norte',
            },
            {
                'name': 'Café Zona Sur',
                'latitude': -34.6200,
                'longitude': -58.3900,
                'radius_meters': 60,
                'description': 'Sucursal en zona sur',
            },
            {
                'name': 'Café Oficinas',
                'latitude': -34.5950,
                'longitude': -58.3750,
                'radius_meters': 40,
                'description': 'Oficinas administrativas',
            },
        ]

        created_count = 0
        for loc_data in locations:
            location = LocationBoundary(**loc_data, is_active=True)
            db.session.add(location)
            created_count += 1
            print(f'✓ Creada ubicación: {location.name}')

        db.session.commit()
        print(f'\n✅ {created_count} ubicaciones creadas exitosamente')

if __name__ == '__main__':
    seed_locations()
