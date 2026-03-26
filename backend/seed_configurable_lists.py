"""
Seed data for ConfigurableList table
Run this script after database migration to populate default values
"""
from app import create_app
from app.extensions import db
from app.models.configurable_list import ConfigurableList

def seed_configurable_lists():
    app = create_app()
    
    with app.app_context():
        print("Seeding ConfigurableList data...")
        
        # Product Categories
        categories = [
            ('product_category', 'Lácteos', 1),
            ('product_category', 'Carnes', 2),
            ('product_category', 'Verduras', 3),
            ('product_category', 'Frutas', 4),
            ('product_category', 'Panadería', 5),
            ('product_category', 'Bebidas', 6),
            ('product_category', 'Limpieza', 7),
            ('product_category', 'Descartables', 8),
            ('product_category', 'Condimentos', 9),
            ('product_category', 'Congelados', 10),
            ('product_category', 'Enlatados', 11),
            ('product_category', 'Granos y Cereales', 12),
            ('product_category', 'Aceites y Grasas', 13),
            ('product_category', 'Otros', 99),
        ]
        
        # Units of Measure
        units = [
            ('unit_of_measure', 'Kilogramo (kg)', 1),
            ('unit_of_measure', 'Gramo (g)', 2),
            ('unit_of_measure', 'Litro (L)', 3),
            ('unit_of_measure', 'Mililitro (ml)', 4),
            ('unit_of_measure', 'Unidad (un)', 5),
            ('unit_of_measure', 'Docena (doc)', 6),
            ('unit_of_measure', 'Caja', 7),
            ('unit_of_measure', 'Paquete (paq)', 8),
            ('unit_of_measure', 'Bolsa', 9),
            ('unit_of_measure', 'Metro (m)', 10),
            ('unit_of_measure', 'Rollo', 11),
        ]
        
        # Payment Terms
        payment_terms = [
            ('payment_terms', 'Contado', 1),
            ('payment_terms', '7 días', 2),
            ('payment_terms', '15 días', 3),
            ('payment_terms', '30 días', 4),
            ('payment_terms', '45 días', 5),
            ('payment_terms', '60 días', 6),
            ('payment_terms', '90 días', 7),
            ('payment_terms', 'Contra entrega', 8),
        ]
        
        all_items = categories + units + payment_terms
        
        for list_type, value, display_order in all_items:
            existing = ConfigurableList.query.filter_by(
                list_type=list_type,
                value=value
            ).first()
            
            if not existing:
                item = ConfigurableList(
                    list_type=list_type,
                    value=value,
                    display_order=display_order,
                    is_active=True
                )
                db.session.add(item)
                print(f"  Added: {list_type} - {value}")
            else:
                print(f"  Skipped (exists): {list_type} - {value}")
        
        db.session.commit()
        print(f"\nSeeding completed! Total items: {len(all_items)}")
        
        # Print summary
        print("\nSummary:")
        for list_type in ['product_category', 'unit_of_measure', 'payment_terms']:
            count = ConfigurableList.query.filter_by(list_type=list_type, is_active=True).count()
            print(f"  {list_type}: {count} active items")

if __name__ == '__main__':
    seed_configurable_lists()
