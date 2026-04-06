"""
Migration script to add extraordinary_amount and extraordinary_description columns to payrolls table.

This script adds support for extraordinary payments (bonuses, deductions, etc.) to payroll records.

Usage:
    python add_extraordinary_fields.py
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

# Fix postgres:// to postgresql:// for SQLAlchemy compatibility
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def main():
    print("Starting migration: Add extraordinary fields to payrolls table")
    print(f"Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Not shown'}")
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            extraordinary_amount_exists = check_column_exists(engine, 'payrolls', 'extraordinary_amount')
            extraordinary_description_exists = check_column_exists(engine, 'payrolls', 'extraordinary_description')
            
            if extraordinary_amount_exists and extraordinary_description_exists:
                print("✓ Columns already exist. No migration needed.")
                return
            
            # Start transaction
            trans = conn.begin()
            
            try:
                # Add extraordinary_amount column if it doesn't exist
                if not extraordinary_amount_exists:
                    print("Adding column: extraordinary_amount")
                    conn.execute(text("""
                        ALTER TABLE payrolls 
                        ADD COLUMN extraordinary_amount NUMERIC(10, 2) DEFAULT 0
                    """))
                    print("✓ Column extraordinary_amount added successfully")
                else:
                    print("✓ Column extraordinary_amount already exists")
                
                # Add extraordinary_description column if it doesn't exist
                if not extraordinary_description_exists:
                    print("Adding column: extraordinary_description")
                    conn.execute(text("""
                        ALTER TABLE payrolls 
                        ADD COLUMN extraordinary_description TEXT
                    """))
                    print("✓ Column extraordinary_description added successfully")
                else:
                    print("✓ Column extraordinary_description already exists")
                
                # Commit transaction
                trans.commit()
                print("\n✓ Migration completed successfully!")
                
            except Exception as e:
                trans.rollback()
                print(f"\n✗ Error during migration: {e}")
                raise
                
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == '__main__':
    main()
