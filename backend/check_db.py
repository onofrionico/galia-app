from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    result = db.session.execute(db.text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'employees' 
        ORDER BY ordinal_position
    """))
    
    print("Columnas en tabla 'employees':")
    for row in result:
        print(f"  - {row[0]}: {row[1]}")
