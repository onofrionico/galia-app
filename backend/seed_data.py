from app import create_app
from app.extensions import db
from app.models.expense import ExpenseCategory

app = create_app()

with app.app_context():
    categories = [
        ExpenseCategory(name='Insumos', description='Café, leche, azúcar, etc.', is_active=True),
        ExpenseCategory(name='Servicios', description='Luz, agua, gas, internet', is_active=True),
        ExpenseCategory(name='Mantenimiento', description='Reparaciones y mantenimiento', is_active=True),
        ExpenseCategory(name='Personal', description='Sueldos y cargas sociales', is_active=True),
        ExpenseCategory(name='Otros', description='Gastos varios', is_active=True),
    ]
    
    for category in categories:
        existing = ExpenseCategory.query.filter_by(name=category.name).first()
        if not existing:
            db.session.add(category)
            print(f"✓ Categoría creada: {category.name}")
        else:
            print(f"- Categoría ya existe: {category.name}")
    
    db.session.commit()
    print("\n✓ Datos iniciales creados exitosamente")
