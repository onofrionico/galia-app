import os
from app import create_app
from app.extensions import db
from app.models.product_category import ProductCategory
from app.models.product import Product
from app.models.product_variant import ProductVariant

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

with app.app_context():
    # Definir categorías
    categories_data = [
        # Bebidas calientes
        {'name': 'Café', 'description': 'Bebidas a base de café'},
        {'name': 'Té', 'description': 'Tés e infusiones'},
        {'name': 'Chocolate Caliente', 'description': 'Chocolates y bebidas calientes'},

        # Bebidas frías
        {'name': 'Jugos Naturales', 'description': 'Jugos frescos y naturales'},
        {'name': 'Bebidas Frías', 'description': 'Refrescos y bebidas heladas'},
        {'name': 'Smoothies', 'description': 'Batidos y smoothies'},

        # Desayunos
        {'name': 'Desayunos Completos', 'description': 'Opciones de desayuno completo'},
        {'name': 'Tostadas y Pan', 'description': 'Pan tostado y sándwiches'},
        {'name': 'Medialunas y Facturas', 'description': 'Medialunas y productos de pastelería'},

        # Almuerzo
        {'name': 'Sándwiches', 'description': 'Sándwiches y bocadillos'},
        {'name': 'Ensaladas', 'description': 'Ensaladas variadas'},
        {'name': 'Platos Principales', 'description': 'Platos principales y pastas'},

        # Postres
        {'name': 'Postres Fríos', 'description': 'Helados y postres fríos'},
        {'name': 'Tortas y Pasteles', 'description': 'Tortas y pasteles caseros'},
        {'name': 'Dulces y Chocolates', 'description': 'Golosinas y chocolates'},
    ]

    # Crear categorías
    categories = {}
    print("[+] Creando categorías...")
    for cat_data in categories_data:
        existing = ProductCategory.query.filter_by(name=cat_data['name']).first()
        if existing:
            categories[cat_data['name']] = existing
            print(f"  [OK] Categoría ya existe: {cat_data['name']}")
        else:
            category = ProductCategory(
                name=cat_data['name'],
                description=cat_data['description'],
                is_active=True
            )
            db.session.add(category)
            categories[cat_data['name']] = category
            print(f"  [OK] Categoría creada: {cat_data['name']}")

    db.session.commit()

    # Definir productos por categoría
    products_data = {
        'Café': [
            {'name': 'Café Espresso', 'price': 2.50},
            {'name': 'Café Americano', 'price': 3.00},
            {'name': 'Café con Leche', 'price': 3.50},
            {'name': 'Cappuccino', 'price': 4.00},
            {'name': 'Latte', 'price': 4.00},
            {'name': 'Macchiato', 'price': 3.75},
            {'name': 'Cortado', 'price': 2.75},
            {'name': 'Café Doble', 'price': 4.50},
        ],
        'Té': [
            {'name': 'Té Negro', 'price': 2.00},
            {'name': 'Té Verde', 'price': 2.00},
            {'name': 'Té Blanco', 'price': 2.50},
            {'name': 'Té de Manzanilla', 'price': 2.00},
            {'name': 'Té de Menta', 'price': 2.00},
            {'name': 'Té de Jengibre', 'price': 2.50},
            {'name': 'Rooibos', 'price': 2.25},
            {'name': 'Té Chai', 'price': 3.00},
        ],
        'Chocolate Caliente': [
            {'name': 'Chocolate Caliente Chico', 'price': 3.00},
            {'name': 'Chocolate Caliente Grande', 'price': 4.00},
            {'name': 'Chocolate con Almendras', 'price': 4.50},
            {'name': 'Chocolate con Avellanas', 'price': 4.50},
            {'name': 'Chocolate Blanco', 'price': 3.50},
        ],
        'Jugos Naturales': [
            {'name': 'Jugo de Naranja', 'price': 3.50},
            {'name': 'Jugo de Pomelo', 'price': 3.50},
            {'name': 'Jugo de Limón', 'price': 2.50},
            {'name': 'Jugo de Manzana', 'price': 3.00},
            {'name': 'Jugo de Uva', 'price': 3.50},
            {'name': 'Jugo Detox', 'price': 4.50},
            {'name': 'Jugo Verde', 'price': 4.50},
        ],
        'Bebidas Frías': [
            {'name': 'Agua Mineral', 'price': 1.50},
            {'name': 'Refresco Cola', 'price': 2.00},
            {'name': 'Refresco Naranja', 'price': 2.00},
            {'name': 'Refresco Limón', 'price': 2.00},
            {'name': 'Té Helado', 'price': 2.50},
            {'name': 'Limonada', 'price': 3.00},
            {'name': 'Cerveza Artesanal', 'price': 5.00},
        ],
        'Smoothies': [
            {'name': 'Smoothie de Fresa', 'price': 4.50},
            {'name': 'Smoothie de Plátano', 'price': 4.00},
            {'name': 'Smoothie de Mango', 'price': 4.50},
            {'name': 'Smoothie Tropical', 'price': 5.00},
            {'name': 'Smoothie Verde', 'price': 5.00},
            {'name': 'Smoothie de Arándanos', 'price': 5.00},
        ],
        'Desayunos Completos': [
            {'name': 'Desayuno Continental', 'price': 8.00},
            {'name': 'Desayuno Americano', 'price': 10.00},
            {'name': 'Desayuno Argentino', 'price': 9.00},
            {'name': 'Desayuno Vegetariano', 'price': 8.50},
        ],
        'Tostadas y Pan': [
            {'name': 'Tostadas Simples', 'price': 2.50},
            {'name': 'Tostadas con Mantequilla', 'price': 3.00},
            {'name': 'Tostadas con Mermelada', 'price': 3.50},
            {'name': 'Tostadas con Queso', 'price': 3.75},
            {'name': 'Sándwich de Jamón y Queso', 'price': 5.00},
            {'name': 'Sándwich de Pechuga', 'price': 6.00},
            {'name': 'Pan Tostado Integral', 'price': 3.00},
        ],
        'Medialunas y Facturas': [
            {'name': 'Medialuna de Manteca', 'price': 1.50},
            {'name': 'Medialuna de Dulce de Leche', 'price': 2.00},
            {'name': 'Medialuna de Chocolate', 'price': 2.00},
            {'name': 'Medialunas x3', 'price': 4.00},
            {'name': 'Churro Relleno', 'price': 2.50},
            {'name': 'Donut de Chocolate', 'price': 2.00},
            {'name': 'Croissant', 'price': 2.50},
        ],
        'Sándwiches': [
            {'name': 'Sándwich Clásico', 'price': 5.00},
            {'name': 'Sándwich de Atún', 'price': 6.00},
            {'name': 'Sándwich Vegetariano', 'price': 5.50},
            {'name': 'Sándwich de Pollo', 'price': 6.50},
            {'name': 'Sándwich de Queso', 'price': 4.50},
            {'name': 'Sándwich Completo', 'price': 7.00},
            {'name': 'Tostado de Jamón y Queso', 'price': 5.50},
            {'name': 'Tostado Mixto', 'price': 6.00},
        ],
        'Ensaladas': [
            {'name': 'Ensalada Verde', 'price': 5.00},
            {'name': 'Ensalada César', 'price': 7.00},
            {'name': 'Ensalada Griega', 'price': 7.50},
            {'name': 'Ensalada de Remolacha', 'price': 6.00},
            {'name': 'Ensalada Caprese', 'price': 6.50},
            {'name': 'Ensalada de Pollo', 'price': 8.00},
        ],
        'Platos Principales': [
            {'name': 'Pasta Bolognesa', 'price': 9.00},
            {'name': 'Pasta Alfredo', 'price': 9.50},
            {'name': 'Pasta Carbonara', 'price': 10.00},
            {'name': 'Pechuga a la Plancha', 'price': 12.00},
            {'name': 'Bisté con Papas', 'price': 14.00},
            {'name': 'Salmón a la Mantequilla', 'price': 15.00},
            {'name': 'Pizza Margherita', 'price': 10.00},
            {'name': 'Pizza Especial', 'price': 12.00},
        ],
        'Postres Fríos': [
            {'name': 'Helado Vainilla', 'price': 3.00},
            {'name': 'Helado Chocolate', 'price': 3.00},
            {'name': 'Helado Fresa', 'price': 3.00},
            {'name': 'Helado Dulce de Leche', 'price': 3.50},
            {'name': 'Helado Menta Chocolate', 'price': 3.50},
            {'name': 'Copón Mixto', 'price': 5.00},
            {'name': 'Postre Tiramisú', 'price': 6.00},
        ],
        'Tortas y Pasteles': [
            {'name': 'Torta de Chocolate', 'price': 4.50},
            {'name': 'Torta Chantilly', 'price': 5.00},
            {'name': 'Torta de Fresa', 'price': 5.50},
            {'name': 'Torta de Tres Leches', 'price': 6.00},
            {'name': 'Bizcochuelo', 'price': 3.50},
            {'name': 'Tartas Variadas', 'price': 4.00},
        ],
        'Dulces y Chocolates': [
            {'name': 'Brownie', 'price': 3.50},
            {'name': 'Chocolate Belga', 'price': 2.50},
            {'name': 'Alfajor', 'price': 2.00},
            {'name': 'Dulce de Leche Artesanal', 'price': 3.00},
            {'name': 'Macarón', 'price': 2.50},
            {'name': 'Bombón de Chocolate', 'price': 2.00},
        ],
    }

    # Crear productos
    print("\n[*] Creando productos...")
    total_products = 0
    for category_name, products in products_data.items():
        category = categories[category_name]
        for product_data in products:
            existing = Product.query.filter_by(name=product_data['name']).first()
            if not existing:
                product = Product(
                    name=product_data['name'],
                    category_id=category.id,
                    is_active=True
                )
                db.session.add(product)
                db.session.flush()  # Para obtener el ID del producto

                # Crear variante por defecto
                variant = ProductVariant(
                    product_id=product.id,
                    name="Tamaño Estándar",
                    price=product_data['price'],
                    is_active=True
                )
                db.session.add(variant)
                total_products += 1
                print(f"  [OK] Producto creado: {product_data['name']} (${product_data['price']}) en {category_name}")

    db.session.commit()

    print(f"\n[DONE] Seed completado:")
    print(f"   * {len(categories)} categorías creadas")
    print(f"   * {total_products} productos creados")
    print(f"\n[STATS] Estadísticas por categoría:")
    for category_name in categories_data:
        count = Product.query.filter_by(category_id=categories[category_name['name']].id).count()
        print(f"   * {category_name['name']}: {count} productos")
