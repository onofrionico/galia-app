from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE job_positions ADD COLUMN IF NOT EXISTS sunday_rate_multiplier NUMERIC(3,2) DEFAULT 1.0'))
        db.session.commit()
        print('✓ Column sunday_rate_multiplier added successfully to job_positions table')
    except Exception as e:
        print(f'Error: {e}')
        db.session.rollback()
