"""
Script para crear las categorías de gastos predeterminadas.
Ejecutar: python seed_expense_categories.py
"""
from app import create_app
from app.extensions import db
from app.models.expense import ExpenseCategory

# Categorías predeterminadas
DEFAULT_CATEGORIES = [
    # Gastos Directos (relacionados con producción/venta)
    {'name': 'Mercadería general', 'description': 'Productos para reventa', 'expense_type': 'directo'},
    {'name': 'Insumos de cocina', 'description': 'Materias primas para preparación', 'expense_type': 'directo'},
    {'name': 'Panificados', 'description': 'Pan, medialunas, tortas, etc.', 'expense_type': 'directo'},
    {'name': 'Bebidas', 'description': 'Bebidas para venta', 'expense_type': 'directo'},
    {'name': 'Verdulería', 'description': 'Frutas y verduras', 'expense_type': 'directo'},
    {'name': 'Lácteos', 'description': 'Leche, quesos, yogurt', 'expense_type': 'directo'},
    {'name': 'Fiambres', 'description': 'Jamón, queso de máquina', 'expense_type': 'directo'},
    
    # Gastos Indirectos (gastos fijos/operativos)
    {'name': 'Alquiler', 'description': 'Alquiler del local', 'expense_type': 'indirecto'},
    {'name': 'Servicios', 'description': 'Luz, gas, agua, internet', 'expense_type': 'indirecto'},
    {'name': 'Contadora', 'description': 'Honorarios contables', 'expense_type': 'indirecto'},
    {'name': 'Marketing', 'description': 'Redes sociales, publicidad, diseño', 'expense_type': 'indirecto'},
    {'name': 'Mantenimiento', 'description': 'Reparaciones y mantenimiento', 'expense_type': 'indirecto'},
    {'name': 'Limpieza', 'description': 'Productos químicos y limpieza', 'expense_type': 'indirecto'},
    {'name': 'Papelería', 'description': 'Artículos de librería y papelería', 'expense_type': 'indirecto'},
    {'name': 'Packaging', 'description': 'Envases, bolsas, servilletas', 'expense_type': 'indirecto'},
    {'name': 'Hielo', 'description': 'Bolsas de hielo', 'expense_type': 'directo'},
    {'name': 'Flores', 'description': 'Decoración con flores', 'expense_type': 'indirecto'},
    {'name': 'Otros', 'description': 'Gastos varios no categorizados', 'expense_type': 'indirecto'},
]


def seed_categories():
    app = create_app()
    
    with app.app_context():
        print("Creando categorías de gastos predeterminadas...")
        
        created = 0
        skipped = 0
        
        for cat_data in DEFAULT_CATEGORIES:
            existing = ExpenseCategory.query.filter_by(name=cat_data['name']).first()
            
            if existing:
                # Actualizar expense_type si es necesario
                if not hasattr(existing, 'expense_type') or existing.expense_type != cat_data['expense_type']:
                    existing.expense_type = cat_data['expense_type']
                    existing.description = cat_data['description']
                    print(f"  Actualizado: {cat_data['name']}")
                else:
                    print(f"  Ya existe: {cat_data['name']}")
                skipped += 1
            else:
                category = ExpenseCategory(
                    name=cat_data['name'],
                    description=cat_data['description'],
                    expense_type=cat_data['expense_type'],
                    is_active=True
                )
                db.session.add(category)
                print(f"  Creado: {cat_data['name']}")
                created += 1
        
        db.session.commit()
        
        print(f"\nResumen: {created} creadas, {skipped} ya existían")
        print("Categorías de gastos configuradas correctamente!")


if __name__ == '__main__':
    seed_categories()
