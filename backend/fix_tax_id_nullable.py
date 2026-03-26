#!/usr/bin/env python3
"""
Script to make tax_id column nullable in suppliers table
Run this script to fix the database constraint
"""
import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/galia_db')

def main():
    try:
        print(f"Connecting to database...")
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            print("Executing ALTER TABLE to make tax_id nullable...")
            conn.execute(text("ALTER TABLE suppliers ALTER COLUMN tax_id DROP NOT NULL;"))
            conn.commit()
            print("✅ Successfully made tax_id column nullable!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
