"""
Migration script to add extraordinary_amount and extraordinary_description fields to payrolls table
These fields can be used for any extraordinary salary concepts (vacations, bonuses, etc.)
"""
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Add extraordinary_amount column
        db.session.execute(text("""
            ALTER TABLE payrolls 
            ADD COLUMN IF NOT EXISTS extraordinary_amount NUMERIC(10, 2) DEFAULT 0
        """))
        
        # Add extraordinary_description column
        db.session.execute(text("""
            ALTER TABLE payrolls 
            ADD COLUMN IF NOT EXISTS extraordinary_description TEXT
        """))
        
        db.session.commit()
        print("✓ Successfully added extraordinary_amount and extraordinary_description columns to payrolls table")
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error adding columns: {e}")
