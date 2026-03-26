from app import create_app
from app.extensions import db
from app.models.expense import ExpenseCategory
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.product_master import ProductMaster
from app.models.price_history import PriceHistory
from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from datetime import datetime, timedelta, date
from decimal import Decimal
import random

app = create_app()

def create_expense_categories():
    """Create expense categories"""
    print("\n=== Creando Categorías de Gastos ===")
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

def create_suppliers():
    """Create test suppliers"""
    print("\n=== Creando Proveedores ===")
    suppliers_data = [
        {
            'name': 'Distribuidora La Abundancia',
            'tax_id': '30-12345678-9',
            'contact_person': 'Juan Pérez',
            'email': 'ventas@laabundancia.com.ar',
            'phone': '+54 11 4567-8901',
            'address': 'Av. Corrientes 1234, CABA',
            'payment_terms': 'Cuenta corriente 30 días',
            'status': 'active'
        },
        {
            'name': 'Café Premium S.A.',
            'tax_id': '30-98765432-1',
            'contact_person': 'María González',
            'email': 'info@cafepremium.com.ar',
            'phone': '+54 11 5678-9012',
            'address': 'Av. Santa Fe 5678, CABA',
            'payment_terms': 'Contado',
            'status': 'active'
        },
        {
            'name': 'Lácteos del Sur',
            'tax_id': '30-11223344-5',
            'contact_person': 'Carlos Rodríguez',
            'email': 'ventas@lacteossur.com.ar',
            'phone': '+54 11 6789-0123',
            'address': 'Ruta 2 Km 45, La Plata',
            'payment_terms': 'Cuenta corriente 15 días',
            'status': 'active'
        },
        {
            'name': 'Pastelería Artesanal',
            'tax_id': '30-55667788-9',
            'contact_person': 'Ana Martínez',
            'email': 'contacto@pasteleria.com.ar',
            'phone': '+54 11 7890-1234',
            'address': 'Av. Cabildo 2345, CABA',
            'payment_terms': 'Contado',
            'status': 'active'
        },
        {
            'name': 'Insumos Gastronómicos',
            'tax_id': '30-99887766-5',
            'contact_person': 'Roberto Silva',
            'email': 'ventas@insumosgastro.com.ar',
            'phone': '+54 11 8901-2345',
            'address': 'Av. Rivadavia 8901, CABA',
            'payment_terms': 'Cuenta corriente 30 días',
            'status': 'active'
        }
    ]
    
    created_suppliers = []
    for supplier_data in suppliers_data:
        existing = Supplier.query.filter_by(tax_id=supplier_data['tax_id']).first()
        if not existing:
            supplier = Supplier(**supplier_data)
            db.session.add(supplier)
            created_suppliers.append(supplier)
            print(f"✓ Proveedor creado: {supplier_data['name']}")
        else:
            created_suppliers.append(existing)
            print(f"- Proveedor ya existe: {supplier_data['name']}")
    
    db.session.commit()
    return created_suppliers

def create_product_masters():
    """Create product masters for cross-supplier comparison"""
    print("\n=== Creando Productos Maestros ===")
    masters_data = [
        {'name': 'Café en Grano', 'category': 'Café', 'unit_of_measure': 'kg'},
        {'name': 'Leche Entera', 'category': 'Lácteos', 'unit_of_measure': 'litro'},
        {'name': 'Azúcar', 'category': 'Endulzantes', 'unit_of_measure': 'kg'},
        {'name': 'Medialunas', 'category': 'Panadería', 'unit_of_measure': 'docena'},
    ]
    
    created_masters = []
    for master_data in masters_data:
        existing = ProductMaster.query.filter_by(name=master_data['name']).first()
        if not existing:
            master = ProductMaster(**master_data)
            db.session.add(master)
            created_masters.append(master)
            print(f"✓ Producto maestro creado: {master_data['name']}")
        else:
            created_masters.append(existing)
            print(f"- Producto maestro ya existe: {master_data['name']}")
    
    db.session.commit()
    return created_masters

def create_products(suppliers, product_masters):
    """Create test products for suppliers"""
    print("\n=== Creando Productos ===")
    
    products_data = [
        # Distribuidora La Abundancia
        {'supplier_idx': 0, 'name': 'Café Torrado Premium', 'sku': 'CAF-001', 'category': 'Café', 
         'unit_of_measure': 'kg', 'price': 3500.00, 'master_idx': 0},
        {'supplier_idx': 0, 'name': 'Azúcar Blanca', 'sku': 'AZU-001', 'category': 'Endulzantes',
         'unit_of_measure': 'kg', 'price': 450.00, 'master_idx': 2},
        {'supplier_idx': 0, 'name': 'Leche Entera Sachet', 'sku': 'LEC-001', 'category': 'Lácteos',
         'unit_of_measure': 'litro', 'price': 380.00, 'master_idx': 1},
        {'supplier_idx': 0, 'name': 'Yerba Mate', 'sku': 'YER-001', 'category': 'Infusiones',
         'unit_of_measure': 'kg', 'price': 1200.00, 'master_idx': None},
        
        # Café Premium S.A.
        {'supplier_idx': 1, 'name': 'Café Arábica Especial', 'sku': 'CAF-ARAB-001', 'category': 'Café',
         'unit_of_measure': 'kg', 'price': 4200.00, 'master_idx': 0},
        {'supplier_idx': 1, 'name': 'Café Blend Premium', 'sku': 'CAF-BLEND-001', 'category': 'Café',
         'unit_of_measure': 'kg', 'price': 3800.00, 'master_idx': 0},
        {'supplier_idx': 1, 'name': 'Té Negro Premium', 'sku': 'TE-NEG-001', 'category': 'Infusiones',
         'unit_of_measure': 'kg', 'price': 2500.00, 'master_idx': None},
        
        # Lácteos del Sur
        {'supplier_idx': 2, 'name': 'Leche Entera Fresca', 'sku': 'LEC-ENT-001', 'category': 'Lácteos',
         'unit_of_measure': 'litro', 'price': 420.00, 'master_idx': 1},
        {'supplier_idx': 2, 'name': 'Leche Descremada', 'sku': 'LEC-DES-001', 'category': 'Lácteos',
         'unit_of_measure': 'litro', 'price': 410.00, 'master_idx': None},
        {'supplier_idx': 2, 'name': 'Crema de Leche', 'sku': 'CRE-001', 'category': 'Lácteos',
         'unit_of_measure': 'litro', 'price': 850.00, 'master_idx': None},
        {'supplier_idx': 2, 'name': 'Dulce de Leche', 'sku': 'DUL-001', 'category': 'Lácteos',
         'unit_of_measure': 'kg', 'price': 1200.00, 'master_idx': None},
        
        # Pastelería Artesanal
        {'supplier_idx': 3, 'name': 'Medialunas de Manteca', 'sku': 'MED-MAN-001', 'category': 'Panadería',
         'unit_of_measure': 'docena', 'price': 1800.00, 'master_idx': 3},
        {'supplier_idx': 3, 'name': 'Croissants', 'sku': 'CRO-001', 'category': 'Panadería',
         'unit_of_measure': 'docena', 'price': 2200.00, 'master_idx': None},
        {'supplier_idx': 3, 'name': 'Facturas Surtidas', 'sku': 'FAC-SUR-001', 'category': 'Panadería',
         'unit_of_measure': 'docena', 'price': 1500.00, 'master_idx': None},
        
        # Insumos Gastronómicos
        {'supplier_idx': 4, 'name': 'Azúcar Refinada', 'sku': 'AZU-REF-001', 'category': 'Endulzantes',
         'unit_of_measure': 'kg', 'price': 480.00, 'master_idx': 2},
        {'supplier_idx': 4, 'name': 'Edulcorante Líquido', 'sku': 'EDU-LIQ-001', 'category': 'Endulzantes',
         'unit_of_measure': 'litro', 'price': 1500.00, 'master_idx': None},
        {'supplier_idx': 4, 'name': 'Servilletas', 'sku': 'SER-001', 'category': 'Descartables',
         'unit_of_measure': 'paquete', 'price': 350.00, 'master_idx': None},
        {'supplier_idx': 4, 'name': 'Vasos Descartables', 'sku': 'VAS-DESC-001', 'category': 'Descartables',
         'unit_of_measure': 'paquete', 'price': 800.00, 'master_idx': None},
    ]
    
    created_products = []
    for prod_data in products_data:
        supplier = suppliers[prod_data['supplier_idx']]
        master = product_masters[prod_data['master_idx']] if prod_data['master_idx'] is not None else None
        
        existing = Product.query.filter_by(
            supplier_id=supplier.id,
            sku=prod_data['sku']
        ).first()
        
        if not existing:
            product = Product(
                supplier_id=supplier.id,
                product_master_id=master.id if master else None,
                name=prod_data['name'],
                sku=prod_data['sku'],
                category=prod_data['category'],
                unit_of_measure=prod_data['unit_of_measure'],
                current_price=Decimal(str(prod_data['price'])),
                status='active'
            )
            db.session.add(product)
            db.session.flush()
            
            # Create initial price history
            price_history = PriceHistory(
                product_id=product.id,
                price=Decimal(str(prod_data['price'])),
                effective_date=date.today() - timedelta(days=90),
                source='manual',
                notes='Precio inicial'
            )
            db.session.add(price_history)
            
            created_products.append(product)
            print(f"✓ Producto creado: {prod_data['name']} ({supplier.name})")
        else:
            created_products.append(existing)
            print(f"- Producto ya existe: {prod_data['name']} ({supplier.name})")
    
    db.session.commit()
    return created_products

def create_purchases(suppliers, products):
    """Create test purchases with items"""
    print("\n=== Creando Compras ===")
    
    # Group products by supplier
    products_by_supplier = {}
    for product in products:
        if product.supplier_id not in products_by_supplier:
            products_by_supplier[product.supplier_id] = []
        products_by_supplier[product.supplier_id].append(product)
    
    created_purchases = []
    
    # Create purchases for the last 3 months
    start_date = datetime.now() - timedelta(days=90)
    
    for supplier in suppliers:
        supplier_products = products_by_supplier.get(supplier.id, [])
        if not supplier_products:
            continue
        
        # Create 5-10 purchases per supplier
        num_purchases = random.randint(5, 10)
        
        for i in range(num_purchases):
            # Random date in the last 90 days
            days_ago = random.randint(0, 90)
            purchase_date = start_date + timedelta(days=days_ago)
            
            # Check if purchase already exists
            existing = Purchase.query.filter_by(
                supplier_id=supplier.id,
                purchase_date=purchase_date.date()
            ).first()
            
            if existing:
                continue
            
            purchase = Purchase(
                supplier_id=supplier.id,
                purchase_date=purchase_date.date(),
                invoice_number=f'FC-{supplier.id:03d}-{i+1:04d}',
                payment_status='completed',
                total_amount=Decimal('0'),
                notes=f'Compra de prueba #{i+1}'
            )
            db.session.add(purchase)
            db.session.flush()
            
            # Add 2-5 random products to this purchase
            num_items = random.randint(2, min(5, len(supplier_products)))
            selected_products = random.sample(supplier_products, num_items)
            
            total_amount = Decimal('0')
            
            for product in selected_products:
                quantity = Decimal(str(random.randint(5, 50)))
                unit_price = product.current_price
                total_price = quantity * unit_price
                
                item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=product.id,
                    product_name_snapshot=product.name,
                    sku_snapshot=product.sku,
                    quantity=quantity,
                    unit_price=unit_price,
                    catalog_price_at_time=unit_price,
                    total_price=total_price
                )
                db.session.add(item)
                total_amount += total_price
            
            purchase.total_amount = total_amount
            created_purchases.append(purchase)
            print(f"✓ Compra creada: {purchase.invoice_number} - {supplier.name} - ${total_amount:.2f}")
    
    db.session.commit()
    return created_purchases

with app.app_context():
    print("\n" + "="*60)
    print("GENERANDO DATOS DE PRUEBA")
    print("="*60)
    
    # Create all test data
    create_expense_categories()
    suppliers = create_suppliers()
    product_masters = create_product_masters()
    products = create_products(suppliers, product_masters)
    purchases = create_purchases(suppliers, products)
    
    print("\n" + "="*60)
    print("✓ DATOS DE PRUEBA CREADOS EXITOSAMENTE")
    print("="*60)
    print(f"\nResumen:")
    print(f"  - Proveedores: {len(suppliers)}")
    print(f"  - Productos Maestros: {len(product_masters)}")
    print(f"  - Productos: {len(products)}")
    print(f"  - Compras: {len(purchases)}")
    print("\n")
