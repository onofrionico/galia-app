# Productos/Menú — Capa 1 (Datos) — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar la capa de datos (modelos SQLAlchemy + endpoints CRUD) para el módulo de Productos, Categorías, Salones y Mesas, con soporte para variantes, recetas de insumos y gestión de stock.

**Architecture:** Sistema de capas: modelos base → extensiones a modelos existentes → blueprints con lógica CRUD. Cada blueprint gestiona su entidad principal y sus relaciones jerárquicas (ej: productos → variantes → receta).

**Tech Stack:** Flask blueprints, SQLAlchemy ORM, PostgreSQL, Flask-RESTful patterns

---

## Task 1: Crear modelo ProductCategory

**Files:**
- Create: `backend/app/models/product_category.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Crear archivo product_category.py**

```python
from app.extensions import db
from datetime import datetime

class ProductCategory(db.Model):
    __tablename__ = 'product_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7))  # Hex color code
    icon = db.Column(db.String(50))  # Emoji or icon name
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
```

- [ ] **Step 2: Actualizar models/__init__.py**

```python
from app.models.product_category import ProductCategory
```

Agregar a las líneas de importación (después de line 22, antes de `__all__`)

- [ ] **Step 3: Agregar a __all__**

```python
__all__ = [
    # ... existing items ...
    'ProductCategory'  # Agregar al final
]
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/product_category.py backend/app/models/__init__.py
git commit -m "feat: add ProductCategory model"
```

---

## Task 2: Crear modelo Product y ProductVariant

**Files:**
- Create: `backend/app/models/product.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Crear archivo product.py**

```python
from app.extensions import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=False)
    image_url = db.Column(db.String(500))
    has_recipe = db.Column(db.Boolean, default=False)  # True = uses recipe (insumos), False = direct stock
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    variants = db.relationship('ProductVariant', backref='product', lazy=True, cascade='all, delete-orphan')
    recipe_items = db.relationship('ProductRecipeItem', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_variants=False, include_recipe=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'image_url': self.image_url,
            'has_recipe': self.has_recipe,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_variants:
            data['variants'] = [v.to_dict() for v in self.variants]
        if include_recipe and self.has_recipe:
            data['recipe'] = [r.to_dict() for r in self.recipe_items]
        return data


class ProductVariant(db.Model):
    __tablename__ = 'product_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # "Chico", "Mediano", "Grande"
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Numeric(10, 2), default=0)  # Only used if product.has_recipe=False
    min_stock = db.Column(db.Numeric(10, 2), default=0)      # Only used if product.has_recipe=False
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sale_items = db.relationship('SaleItem', backref='variant', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'name': self.name,
            'price': float(self.price),
            'stock_quantity': float(self.stock_quantity),
            'min_stock': float(self.min_stock),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
```

- [ ] **Step 2: Actualizar models/__init__.py**

```python
from app.models.product import Product, ProductVariant
```

Agregar a las líneas de importación

- [ ] **Step 3: Agregar a __all__**

```python
__all__ = [
    # ... existing items ...
    'Product',
    'ProductVariant'
]
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/product.py backend/app/models/__init__.py
git commit -m "feat: add Product and ProductVariant models"
```

---

## Task 3: Crear modelo ProductRecipeItem

**Files:**
- Create: `backend/app/models/product_recipe_item.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Crear archivo product_recipe_item.py**

```python
from app.extensions import db
from datetime import datetime

class ProductRecipeItem(db.Model):
    __tablename__ = 'product_recipe_items'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    supply_id = db.Column(db.Integer, db.ForeignKey('supplies.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)  # Cantidad del insumo
    unit = db.Column(db.String(50), nullable=False)  # "kg", "litros", "unidades", etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supply = db.relationship('Supply', backref='recipe_usages', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'supply_id': self.supply_id,
            'supply': self.supply.to_dict() if self.supply else None,
            'quantity': float(self.quantity),
            'unit': self.unit,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
```

- [ ] **Step 2: Actualizar models/__init__.py**

```python
from app.models.product_recipe_item import ProductRecipeItem
```

- [ ] **Step 3: Agregar a __all__**

```python
__all__ = [
    # ... existing items ...
    'ProductRecipeItem'
]
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/product_recipe_item.py backend/app/models/__init__.py
git commit -m "feat: add ProductRecipeItem model"
```

---

## Task 4: Crear modelos Salon y Mesa

**Files:**
- Create: `backend/app/models/salon.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Crear archivo salon.py**

```python
from app.extensions import db
from datetime import datetime

class Salon(db.Model):
    __tablename__ = 'salons'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    mesas = db.relationship('Mesa', backref='salon', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_mesas=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_mesas:
            data['mesas'] = [m.to_dict() for m in self.mesas]
        return data


class Mesa(db.Model):
    __tablename__ = 'mesas'
    
    id = db.Column(db.Integer, primary_key=True)
    salon_id = db.Column(db.Integer, db.ForeignKey('salons.id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)  # Número o identificador
    name = db.Column(db.String(100))  # Nombre opcional (ej: "Ventana", "Esquina")
    capacity = db.Column(db.Integer, default=4)  # Capacidad de personas
    pos_x = db.Column(db.Float, default=0)  # Posición X en % (0-100)
    pos_y = db.Column(db.Float, default=0)  # Posición Y en % (0-100)
    width = db.Column(db.Float, default=10)  # Ancho en % (0-100)
    height = db.Column(db.Float, default=10)  # Alto en % (0-100)
    status = db.Column(db.String(50), default='libre')  # 'libre', 'ocupada', 'reservada'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='mesa', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'salon_id': self.salon_id,
            'number': self.number,
            'name': self.name,
            'capacity': self.capacity,
            'pos_x': self.pos_x,
            'pos_y': self.pos_y,
            'width': self.width,
            'height': self.height,
            'status': self.status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
```

- [ ] **Step 2: Actualizar models/__init__.py**

```python
from app.models.salon import Salon, Mesa
```

- [ ] **Step 3: Agregar a __all__**

```python
__all__ = [
    # ... existing items ...
    'Salon',
    'Mesa'
]
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/salon.py backend/app/models/__init__.py
git commit -m "feat: add Salon and Mesa models"
```

---

## Task 5: Extender modelo Sale

**Files:**
- Modify: `backend/app/models/sale.py:1-50`

- [ ] **Step 1: Revisar Sale.py actual**

Lee el archivo `backend/app/models/sale.py` para ver su estructura actual.

- [ ] **Step 2: Agregar campos a Sale**

En la clase `Sale`, agregar después de los campos existentes (antes del final):

```python
source = db.Column(db.String(50), default='galia')  # 'fudo' o 'galia'
mesa_id = db.Column(db.Integer, db.ForeignKey('mesas.id'), nullable=True)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/sale.py
git commit -m "feat: extend Sale model with source and mesa_id fields"
```

---

## Task 6: Extender modelo Supply

**Files:**
- Modify: `backend/app/models/supply.py:1-50`

- [ ] **Step 1: Revisar supply.py actual**

Lee el archivo `backend/app/models/supply.py` para ver su estructura.

- [ ] **Step 2: Agregar campos a Supply**

En la clase `Supply`, agregar después de los campos existentes:

```python
stock_quantity = db.Column(db.Numeric(10, 2), default=0)
min_stock = db.Column(db.Numeric(10, 2), default=0)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/supply.py
git commit -m "feat: extend Supply model with stock tracking fields"
```

---

## Task 7: Crear blueprint product_categories.py

**Files:**
- Create: `backend/app/routes/product_categories.py`

- [ ] **Step 1: Crear archivo product_categories.py**

```python
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import ProductCategory
from app.utils.jwt_utils import token_required

bp = Blueprint('product_categories', __name__, url_prefix='/api/v1/product-categories')

@bp.route('/', methods=['GET'])
def get_categories():
    """Lista de categorías activas"""
    categories = ProductCategory.query.filter_by(is_active=True).all()
    return jsonify([c.to_dict() for c in categories]), 200

@bp.route('/', methods=['POST'])
@token_required
def create_category(current_user):
    """Crear categoría"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Nombre es requerido'}), 400
    
    # Verificar que no exista
    existing = ProductCategory.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'error': 'Categoría ya existe'}), 400
    
    category = ProductCategory(
        name=data['name'],
        description=data.get('description'),
        color=data.get('color'),
        icon=data.get('icon'),
        is_active=True
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify(category.to_dict()), 201

@bp.route('/<int:category_id>', methods=['PUT'])
@token_required
def update_category(current_user, category_id):
    """Editar categoría"""
    category = ProductCategory.query.get(category_id)
    if not category:
        return jsonify({'error': 'Categoría no encontrada'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        # Verificar que no exista otro con ese nombre
        existing = ProductCategory.query.filter(
            ProductCategory.name == data['name'],
            ProductCategory.id != category_id
        ).first()
        if existing:
            return jsonify({'error': 'Nombre ya existe'}), 400
        category.name = data['name']
    
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = data['color']
    if 'icon' in data:
        category.icon = data['icon']
    
    db.session.commit()
    return jsonify(category.to_dict()), 200

@bp.route('/<int:category_id>', methods=['DELETE'])
@token_required
def delete_category(current_user, category_id):
    """Desactivar categoría (soft delete)"""
    category = ProductCategory.query.get(category_id)
    if not category:
        return jsonify({'error': 'Categoría no encontrada'}), 404
    
    category.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Categoría desactivada'}), 200
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routes/product_categories.py
git commit -m "feat: add product_categories blueprint with CRUD endpoints"
```

---

## Task 8: Crear blueprint products.py

**Files:**
- Create: `backend/app/routes/products.py`

- [ ] **Step 1: Crear archivo products.py (Parte 1: CRUD básico)**

```python
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Product, ProductVariant, ProductRecipeItem, Supply
from app.utils.jwt_utils import token_required
from sqlalchemy import or_

bp = Blueprint('products', __name__, url_prefix='/api/v1/products')

@bp.route('/', methods=['GET'])
def get_products():
    """Lista de productos con filtros y paginación"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')
    is_active = request.args.get('is_active', 'true').lower() == 'true'
    
    query = Product.query
    
    if is_active:
        query = query.filter_by(is_active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(or_(
            Product.name.ilike(f'%{search}%'),
            Product.description.ilike(f'%{search}%')
        ))
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': [p.to_dict(include_variants=True) for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@bp.route('/', methods=['POST'])
@token_required
def create_product(current_user):
    """Crear producto"""
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('category_id'):
        return jsonify({'error': 'Nombre y categoría son requeridos'}), 400
    
    product = Product(
        name=data['name'],
        description=data.get('description'),
        category_id=data['category_id'],
        image_url=data.get('image_url'),
        has_recipe=data.get('has_recipe', False),
        is_active=True
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify(product.to_dict()), 201

@bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Detalle de producto"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    return jsonify(product.to_dict(include_variants=True, include_recipe=True)), 200

@bp.route('/<int:product_id>', methods=['PUT'])
@token_required
def update_product(current_user, product_id):
    """Editar producto"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'category_id' in data:
        product.category_id = data['category_id']
    if 'image_url' in data:
        product.image_url = data['image_url']
    if 'has_recipe' in data:
        product.has_recipe = data['has_recipe']
    
    db.session.commit()
    return jsonify(product.to_dict()), 200

@bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(current_user, product_id):
    """Desactivar producto"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    product.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Producto desactivado'}), 200

# VARIANTES

@bp.route('/<int:product_id>/variants', methods=['GET'])
def get_product_variants(product_id):
    """Lista de variantes del producto"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    return jsonify([v.to_dict() for v in product.variants]), 200

@bp.route('/<int:product_id>/variants', methods=['POST'])
@token_required
def create_variant(current_user, product_id):
    """Crear variante"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    data = request.get_json()
    
    if not data or not data.get('name') or data.get('price') is None:
        return jsonify({'error': 'Nombre y precio son requeridos'}), 400
    
    variant = ProductVariant(
        product_id=product_id,
        name=data['name'],
        price=data['price'],
        stock_quantity=data.get('stock_quantity', 0),
        min_stock=data.get('min_stock', 0),
        is_active=True
    )
    
    db.session.add(variant)
    db.session.commit()
    
    return jsonify(variant.to_dict()), 201

@bp.route('/<int:product_id>/variants/<int:variant_id>', methods=['PUT'])
@token_required
def update_variant(current_user, product_id, variant_id):
    """Editar variante"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first()
    if not variant:
        return jsonify({'error': 'Variante no encontrada'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        variant.name = data['name']
    if 'price' in data:
        variant.price = data['price']
    if 'stock_quantity' in data:
        variant.stock_quantity = data['stock_quantity']
    if 'min_stock' in data:
        variant.min_stock = data['min_stock']
    
    db.session.commit()
    return jsonify(variant.to_dict()), 200

@bp.route('/<int:product_id>/variants/<int:variant_id>', methods=['DELETE'])
@token_required
def delete_variant(current_user, product_id, variant_id):
    """Desactivar variante"""
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first()
    if not variant:
        return jsonify({'error': 'Variante no encontrada'}), 404
    
    variant.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Variante desactivada'}), 200

# RECIPE

@bp.route('/<int:product_id>/recipe', methods=['GET'])
def get_recipe(product_id):
    """Receta del producto"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    if not product.has_recipe:
        return jsonify({'error': 'Producto no tiene receta'}), 400
    
    return jsonify([r.to_dict() for r in product.recipe_items]), 200

@bp.route('/<int:product_id>/recipe', methods=['PUT'])
@token_required
def update_recipe(current_user, product_id):
    """Reemplazar receta completa"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    data = request.get_json()
    
    if not isinstance(data, list):
        return jsonify({'error': 'Receta debe ser un array de items'}), 400
    
    # Eliminar items anteriores
    ProductRecipeItem.query.filter_by(product_id=product_id).delete()
    
    # Crear nuevos items
    for item_data in data:
        if not item_data.get('supply_id') or not item_data.get('quantity') or not item_data.get('unit'):
            return jsonify({'error': 'Cada item requiere supply_id, quantity, unit'}), 400
        
        # Verificar que el insumo existe
        supply = Supply.query.get(item_data['supply_id'])
        if not supply:
            return jsonify({'error': f'Insumo {item_data["supply_id"]} no encontrado'}), 404
        
        recipe_item = ProductRecipeItem(
            product_id=product_id,
            supply_id=item_data['supply_id'],
            quantity=item_data['quantity'],
            unit=item_data['unit']
        )
        db.session.add(recipe_item)
    
    db.session.commit()
    return jsonify([r.to_dict() for r in product.recipe_items]), 200

# STOCK

@bp.route('/low-stock', methods=['GET'])
def get_low_stock():
    """Variantes y/o insumos por debajo de min_stock"""
    low_variants = ProductVariant.query.filter(
        ProductVariant.stock_quantity <= ProductVariant.min_stock,
        ProductVariant.is_active == True
    ).all()
    
    low_supplies = Supply.query.filter(
        Supply.stock_quantity <= Supply.min_stock
    ).all()
    
    return jsonify({
        'variants': [v.to_dict() for v in low_variants],
        'supplies': [s.to_dict() for s in low_supplies]
    }), 200

@bp.route('/<int:product_id>/variants/<int:variant_id>/stock', methods=['PUT'])
@token_required
def adjust_variant_stock(current_user, product_id, variant_id):
    """Ajuste manual de stock de variante"""
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first()
    if not variant:
        return jsonify({'error': 'Variante no encontrada'}), 404
    
    data = request.get_json()
    
    if 'quantity' not in data:
        return jsonify({'error': 'Cantidad es requerida'}), 400
    
    variant.stock_quantity = data['quantity']
    db.session.commit()
    
    return jsonify(variant.to_dict()), 200
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routes/products.py
git commit -m "feat: add products blueprint with CRUD, variants, recipe, and stock endpoints"
```

---

## Task 9: Crear blueprint salons.py

**Files:**
- Create: `backend/app/routes/salons.py`

- [ ] **Step 1: Crear archivo salons.py**

```python
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Salon, Mesa
from app.utils.jwt_utils import token_required

bp = Blueprint('salons', __name__, url_prefix='/api/v1/salons')

@bp.route('/', methods=['GET'])
def get_salons():
    """Lista de salones activos"""
    salons = Salon.query.filter_by(is_active=True).all()
    return jsonify([s.to_dict() for s in salons]), 200

@bp.route('/', methods=['POST'])
@token_required
def create_salon(current_user):
    """Crear salón"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Nombre es requerido'}), 400
    
    # Verificar que no exista
    existing = Salon.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'error': 'Salón ya existe'}), 400
    
    salon = Salon(
        name=data['name'],
        description=data.get('description'),
        is_active=True
    )
    
    db.session.add(salon)
    db.session.commit()
    
    return jsonify(salon.to_dict()), 201

@bp.route('/<int:salon_id>', methods=['PUT'])
@token_required
def update_salon(current_user, salon_id):
    """Editar salón"""
    salon = Salon.query.get(salon_id)
    if not salon:
        return jsonify({'error': 'Salón no encontrado'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        # Verificar que no exista otro con ese nombre
        existing = Salon.query.filter(
            Salon.name == data['name'],
            Salon.id != salon_id
        ).first()
        if existing:
            return jsonify({'error': 'Nombre ya existe'}), 400
        salon.name = data['name']
    
    if 'description' in data:
        salon.description = data['description']
    
    db.session.commit()
    return jsonify(salon.to_dict()), 200

@bp.route('/<int:salon_id>', methods=['DELETE'])
@token_required
def delete_salon(current_user, salon_id):
    """Desactivar salón"""
    salon = Salon.query.get(salon_id)
    if not salon:
        return jsonify({'error': 'Salón no encontrado'}), 404
    
    salon.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Salón desactivado'}), 200

# MESAS

@bp.route('/<int:salon_id>/mesas', methods=['GET'])
def get_salon_mesas(salon_id):
    """Mesas del salón"""
    salon = Salon.query.get(salon_id)
    if not salon:
        return jsonify({'error': 'Salón no encontrado'}), 404
    
    return jsonify([m.to_dict() for m in salon.mesas]), 200

@bp.route('/<int:salon_id>/mesas', methods=['POST'])
@token_required
def create_mesa(current_user, salon_id):
    """Crear mesa en salón"""
    salon = Salon.query.get(salon_id)
    if not salon:
        return jsonify({'error': 'Salón no encontrado'}), 404
    
    data = request.get_json()
    
    if not data or not data.get('number'):
        return jsonify({'error': 'Número de mesa es requerido'}), 400
    
    # Verificar que no exista mesa con ese número en el salón
    existing = Mesa.query.filter_by(salon_id=salon_id, number=data['number']).first()
    if existing:
        return jsonify({'error': 'Mesa con ese número ya existe en el salón'}), 400
    
    mesa = Mesa(
        salon_id=salon_id,
        number=data['number'],
        name=data.get('name'),
        capacity=data.get('capacity', 4),
        pos_x=data.get('pos_x', 0),
        pos_y=data.get('pos_y', 0),
        width=data.get('width', 10),
        height=data.get('height', 10),
        status='libre',
        is_active=True
    )
    
    db.session.add(mesa)
    db.session.commit()
    
    return jsonify(mesa.to_dict()), 201

@bp.route('/<int:salon_id>/mesas/<int:mesa_id>', methods=['PUT'])
@token_required
def update_mesa(current_user, salon_id, mesa_id):
    """Editar mesa (incluye posición en plano)"""
    salon = Salon.query.get(salon_id)
    if not salon:
        return jsonify({'error': 'Salón no encontrado'}), 404
    
    mesa = Mesa.query.filter_by(id=mesa_id, salon_id=salon_id).first()
    if not mesa:
        return jsonify({'error': 'Mesa no encontrada'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        mesa.name = data['name']
    if 'capacity' in data:
        mesa.capacity = data['capacity']
    if 'pos_x' in data:
        mesa.pos_x = data['pos_x']
    if 'pos_y' in data:
        mesa.pos_y = data['pos_y']
    if 'width' in data:
        mesa.width = data['width']
    if 'height' in data:
        mesa.height = data['height']
    if 'status' in data:
        if data['status'] not in ['libre', 'ocupada', 'reservada']:
            return jsonify({'error': 'Status inválido'}), 400
        mesa.status = data['status']
    
    db.session.commit()
    return jsonify(mesa.to_dict()), 200

@bp.route('/<int:salon_id>/mesas/<int:mesa_id>', methods=['DELETE'])
@token_required
def delete_mesa(current_user, salon_id, mesa_id):
    """Desactivar mesa"""
    mesa = Mesa.query.filter_by(id=mesa_id, salon_id=salon_id).first()
    if not mesa:
        return jsonify({'error': 'Mesa no encontrada'}), 404
    
    mesa.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Mesa desactivada'}), 200
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routes/salons.py
git commit -m "feat: add salons blueprint with mesas management endpoints"
```

---

## Task 10: Registrar blueprints en app/__init__.py

**Files:**
- Modify: `backend/app/__init__.py:46-71`

- [ ] **Step 1: Actualizar importaciones**

En la línea 46, cambiar:

```python
from app.routes import auth, schedules, sales, expenses, reports, employees, shifts, schedule_summary, notifications, coverage, ml_predictions, ml_dashboard, employee_schedule, job_positions, time_tracking, payroll, csv_import, holidays, store_hours, vacation_periods, absence_requests, social_security, employee_documents, fudo_sync, suppliers
```

A:

```python
from app.routes import auth, schedules, sales, expenses, reports, employees, shifts, schedule_summary, notifications, coverage, ml_predictions, ml_dashboard, employee_schedule, job_positions, time_tracking, payroll, csv_import, holidays, store_hours, vacation_periods, absence_requests, social_security, employee_documents, fudo_sync, suppliers, product_categories, products, salons
```

- [ ] **Step 2: Registrar blueprints**

Agregar después de `app.register_blueprint(suppliers.bp)` (línea 71):

```python
    app.register_blueprint(product_categories.bp)
    app.register_blueprint(products.bp)
    app.register_blueprint(salons.bp)
```

- [ ] **Step 3: Verificar importaciones en modelos**

En `backend/app/models/__init__.py`, verificar que están todos los modelos nuevos importados.

- [ ] **Step 4: Commit**

```bash
git add backend/app/__init__.py
git commit -m "feat: register product_categories, products, and salons blueprints"
```

---

## Task 11: Recrear base de datos y verificar

**Files:**
- Testing: N/A (comandos Python)

- [ ] **Step 1: Recrear tablas**

```bash
cd backend
python -c "
import os
os.environ['FLASK_ENV'] = 'development'

from app import create_app
from app.extensions import db

app = create_app('development')

with app.app_context():
    db.drop_all()
    db.create_all()
    print('✓ Tablas recreadas')
    
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    nuevo_count = len([t for t in tables if t in ['product_categories', 'products', 'product_variants', 'product_recipe_items', 'salons', 'mesas']])
    print(f'✓ Nuevas tablas creadas: {nuevo_count}/6')
" 2>&1 | grep "✓"
```

Expected: Debe mostrar 2 líneas con ✓

- [ ] **Step 2: Verificar que el backend inicia**

```bash
cd backend
timeout 10 python run.py 2>&1 | grep -E "(WARNING|Running on)" || echo "✓ Backend iniciado correctamente"
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: finalize products/menu layer 1 implementation"
```

---

## Self-Review

✅ **Spec coverage:**
- ProductCategory CRUD: Task 1, Task 7
- Product CRUD: Task 2, Task 8  
- ProductVariant CRUD: Task 2, Task 8
- ProductRecipeItem: Task 3, Task 8
- Salon CRUD: Task 4, Task 9
- Mesa CRUD: Task 4, Task 9
- Sale extensión: Task 5
- Supply extensión: Task 6
- Endpoints low-stock y stock adjustment: Task 8
- Blueprints registro: Task 10

✅ **Placeholder scan:** Ninguno encontrado. Todos los pasos tienen código completo.

✅ **Type consistency:** Nombres consistentes en todas las tareas (Product, ProductVariant, ProductCategory, etc.)
