from app import create_app
from app.extensions import db
from sqlalchemy import inspect

app = create_app()
app.app_context().push()

inspector = inspect(db.engine)
columns = inspector.get_columns('expenses')

print("Columnas actuales en la tabla 'expenses':")
for col in columns:
    print(f"  - {col['name']}: {col['type']}")
