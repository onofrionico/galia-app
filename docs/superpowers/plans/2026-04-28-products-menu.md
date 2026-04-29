# Productos / Menú — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar la gestión de menú y ventas de Fudo POS con un catálogo de productos propio, POS táctil con plano de salones y control de stock híbrido en Galia.

**Architecture:** Backend Flask con 7 modelos nuevos (ProductCategory, Product, ProductVariant, ProductRecipeItem, SaleItem, Salon, Mesa) y extensiones a Sale y Supply. Cuatro blueprints nuevos (product_categories, products, salons, sales extendido) con servicio de stock centralizado. Frontend React con páginas /pos, /products, /product-categories, /stock y componentes POS.

**Tech Stack:** Flask/SQLAlchemy/Alembic, pytest, React 18, Tailwind CSS, lucide-react, axios.

---

## File Map

### Backend — nuevos
| Archivo | Responsabilidad |
|---|---|
| `backend/app/models/product_category.py` | Modelo ProductCategory |
| `backend/app/models/product.py` | Modelo Product |
| `backend/app/models/product_variant.py` | Modelo ProductVariant |
| `backend/app/models/product_recipe_item.py` | Modelo ProductRecipeItem |
| `backend/app/models/sale_item.py` | Modelo SaleItem |
| `backend/app/models/salon.py` | Modelo Salon |
| `backend/app/models/mesa.py` | Modelo Mesa |
| `backend/app/routes/product_categories.py` | CRUD categorías |
| `backend/app/routes/products.py` | CRUD productos, variantes, receta, stock |
| `backend/app/routes/salons.py` | CRUD salones y mesas |
| `backend/app/services/stock_service.py` | Lógica de descuento de stock |
| `backend/tests/test_product_categories.py` | Tests categorías |
| `backend/tests/test_products.py` | Tests productos |
| `backend/tests/test_salons.py` | Tests salones |
| `backend/tests/test_sales_products.py` | Tests ventas con ítems y stock |

### Backend — modificados
| Archivo | Cambio |
|---|---|
| `backend/app/models/sale.py` | + `source`, `mesa_id`, relación `items` |
| `backend/app/models/supply.py` | + `stock_quantity`, `min_stock` |
| `backend/app/routes/sales.py` | + POST /, GET /:id, GET /daily-summary, GET /top-products |
| `backend/app/__init__.py` | Registrar los 3 blueprints nuevos |

### Frontend — nuevos
| Archivo | Responsabilidad |
|---|---|
| `frontend/src/services/productsService.js` | API client productos |
| `frontend/src/services/productCategoriesService.js` | API client categorías |
| `frontend/src/services/salonsService.js` | API client salones/mesas |
| `frontend/src/services/salesService.js` | API client ventas (incluyendo createSale) |
| `frontend/src/pages/ProductCategories.jsx` | CRUD categorías |
| `frontend/src/pages/Products.jsx` | Lista de productos |
| `frontend/src/pages/ProductDetail.jsx` | Detalle con tabs Info/Variantes/Receta/Historial |
| `frontend/src/pages/Pos.jsx` | Plano de salones + POS |
| `frontend/src/pages/Stock.jsx` | Inventario unificado |
| `frontend/src/components/pos/MesaCard.jsx` | Tarjeta de mesa con estado |
| `frontend/src/components/pos/SalonFloorPlan.jsx` | Plano posicional del salón |
| `frontend/src/components/pos/PosModal.jsx` | Modal grilla de productos + comanda |
| `frontend/src/components/pos/OrderDrawer.jsx` | Drawer comanda activa |
| `frontend/src/components/pos/FloorPlanEditor.jsx` | Modo drag-and-drop edición plano |

### Frontend — modificados
| Archivo | Cambio |
|---|---|
| `frontend/src/components/layout/Sidebar.jsx` | + grupo "Menú" con 4 items |
| `frontend/src/App.jsx` | + 5 rutas nuevas |

---

## Task 1: Modelos SQLAlchemy

**Files:**
- Create: `backend/app/models/product_category.py`
- Create: `backend/app/models/product.py`
- Create: `backend/app/models/product_variant.py`
- Create: `backend/app/models/product_recipe_item.py`
- Create: `backend/app/models/sale_item.py`
- Create: `backend/app/models/salon.py`
- Create: `backend/app/models/mesa.py`
- Modify: `backend/app/models/sale.py`
- Modify: `backend/app/models/supply.py`

- [ ] **Step 1: Crear `backend/app/models/product_category.py`**

```python
from datetime import datetime
from app.extensions import db

class ProductCategory(db.Model):
    __tablename__ = 'product_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(20), nullable=True)
    icon = db.Column(db.String(10), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    products = db.relationship('Product', backref='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
```

- [ ] **Step 2: Crear `backend/app/models/product.py`**

```python
from datetime import datetime
from app.extensions import db

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    has_recipe = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    variants = db.relationship('ProductVariant', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    recipe_items = db.relationship('ProductRecipeItem', backref='product', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'category_color': self.category.color if self.category else None,
            'category_icon': self.category.icon if self.category else None,
            'image_url': self.image_url,
            'has_recipe': self.has_recipe,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
```

- [ ] **Step 3: Crear `backend/app/models/product_variant.py`**

```python
from datetime import datetime
from app.extensions import db

class ProductVariant(db.Model):
    __tablename__ = 'product_variants'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Numeric(10, 3), nullable=False, default=0)
    min_stock = db.Column(db.Numeric(10, 3), nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

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
            'updated_at': self.updated_at.isoformat(),
        }
```

- [ ] **Step 4: Crear `backend/app/models/product_recipe_item.py`**

```python
from app.extensions import db

class ProductRecipeItem(db.Model):
    __tablename__ = 'product_recipe_items'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    supply_id = db.Column(db.Integer, db.ForeignKey('supplies.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 4), nullable=False)
    unit = db.Column(db.String(50), nullable=False)

    supply = db.relationship('Supply', backref='recipe_uses')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'supply_id': self.supply_id,
            'supply_name': self.supply.name if self.supply else None,
            'supply_unit': self.supply.unit if self.supply else None,
            'quantity': float(self.quantity),
            'unit': self.unit,
        }
```

- [ ] **Step 5: Crear `backend/app/models/sale_item.py`**

```python
from app.extensions import db

class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)

    variant = db.relationship('ProductVariant', backref='sale_items')

    def to_dict(self):
        product = self.variant.product if self.variant else None
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'product_variant_id': self.product_variant_id,
            'product_name': product.name if product else None,
            'variant_name': self.variant.name if self.variant else None,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'subtotal': float(self.subtotal),
        }
```

- [ ] **Step 6: Crear `backend/app/models/salon.py`**

```python
from datetime import datetime
from app.extensions import db

class Salon(db.Model):
    __tablename__ = 'salones'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    mesas = db.relationship('Mesa', backref='salon', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
```

- [ ] **Step 7: Crear `backend/app/models/mesa.py`**

```python
from datetime import datetime
from app.extensions import db

class Mesa(db.Model):
    __tablename__ = 'mesas'

    id = db.Column(db.Integer, primary_key=True)
    salon_id = db.Column(db.Integer, db.ForeignKey('salones.id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    capacity = db.Column(db.Integer, nullable=True)
    pos_x = db.Column(db.Float, nullable=False, default=10.0)
    pos_y = db.Column(db.Float, nullable=False, default=10.0)
    width = db.Column(db.Float, nullable=False, default=10.0)
    height = db.Column(db.Float, nullable=False, default=10.0)
    status = db.Column(db.String(20), nullable=False, default='libre')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

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
            'updated_at': self.updated_at.isoformat(),
        }
```

- [ ] **Step 8: Extender `backend/app/models/sale.py`**

Agregar al final de los campos existentes (antes de `__table_args__`) y al final de `to_dict()`:

```python
# Agregar después de `id_origen`:
source = db.Column(db.String(20), nullable=False, default='fudo')
mesa_id = db.Column(db.Integer, db.ForeignKey('mesas.id'), nullable=True)

items = db.relationship('SaleItem', backref='sale', lazy='dynamic', cascade='all, delete-orphan')
```

En `to_dict()` agregar al dict retornado:
```python
'source': self.source,
'mesa_id': self.mesa_id,
```

- [ ] **Step 9: Extender `backend/app/models/supply.py`**

Agregar después de `is_active`:

```python
stock_quantity = db.Column(db.Numeric(10, 3), nullable=False, default=0)
min_stock = db.Column(db.Numeric(10, 3), nullable=False, default=0)
```

En `to_dict()` agregar:
```python
'stock_quantity': float(self.stock_quantity),
'min_stock': float(self.min_stock),
```

- [ ] **Step 10: Verificar que los modelos importan sin error**

```bash
cd backend
source venv/bin/activate
python -c "
from app import create_app
from app.models.product_category import ProductCategory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.product_recipe_item import ProductRecipeItem
from app.models.sale_item import SaleItem
from app.models.salon import Salon
from app.models.mesa import Mesa
app = create_app('testing')
with app.app_context():
    from app.extensions import db
    db.create_all()
    print('OK - todos los modelos se importan y crean tablas')
    db.drop_all()
"
```

Resultado esperado: `OK - todos los modelos se importan y crean tablas`

- [ ] **Step 11: Commit**

```bash
git add backend/app/models/product_category.py \
        backend/app/models/product.py \
        backend/app/models/product_variant.py \
        backend/app/models/product_recipe_item.py \
        backend/app/models/sale_item.py \
        backend/app/models/salon.py \
        backend/app/models/mesa.py \
        backend/app/models/sale.py \
        backend/app/models/supply.py
git commit -m "feat: add product/menu/salon/mesa models and extend Sale and Supply"
```

---

## Task 2: Migración Alembic

**Files:**
- Generate: `backend/migrations/versions/XXXX_add_products_menu_models.py`

- [ ] **Step 1: Crear la migración automática**

```bash
cd backend
source venv/bin/activate
flask db migrate -m "Add products menu models (ProductCategory, Product, ProductVariant, ProductRecipeItem, SaleItem, Salon, Mesa) and extend Sale/Supply"
```

Resultado esperado: nuevo archivo en `backend/migrations/versions/` con el patrón `XXXX_add_products_menu_models.py`

- [ ] **Step 2: Revisar y ajustar la migración (si es necesario)**

Abrir el archivo generado. Verificar que contiene:
- CreateTable para: product_categories, products, product_variants, product_recipe_items, sale_items, salones, mesas
- AddColumn para Sale: `source`, `mesa_id` (con FK a mesas.id)
- AddColumn para Supply: `stock_quantity`, `min_stock`
- CreateForeignKey para todas las relaciones
- CreateIndex si es necesario

Si hay errores de sintaxis o omisiones, editar manualmente.

- [ ] **Step 3: Aplicar la migración**

```bash
cd backend
flask db upgrade
```

Resultado esperado: todas las tablas creadas en PostgreSQL sin errores.

- [ ] **Step 4: Verificar que las tablas existen**

```bash
psql -d galia_dev -c "\dt product_categories products product_variants product_recipe_items sale_items salones mesas"
```

Resultado esperado: 7 tablas listadas.

- [ ] **Step 5: Commit**

```bash
git add backend/migrations/versions/*.py
git commit -m "migration: add products/menu/salon models and extend Sale/Supply"
```

---

## Task 3: Blueprint product_categories + tests

**Files:**
- Create: `backend/app/routes/product_categories.py`
- Create: `backend/tests/test_product_categories.py`
- Modify: `backend/app/__init__.py`

- [ ] **Step 1: Crear `backend/app/routes/product_categories.py`**

```python
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.product_category import ProductCategory
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required
from sqlalchemy.exc import IntegrityError

bp = Blueprint('product_categories', __name__, url_prefix='/api/v1/product-categories')


@bp.route('', methods=['GET'])
@token_required
def list_categories(current_user):
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    
    query = ProductCategory.query
    if not include_inactive:
        query = query.filter(ProductCategory.is_active == True)
    
    categories = query.order_by(ProductCategory.name).all()
    return jsonify({'categories': [c.to_dict() for c in categories], 'total': len(categories)}), 200


@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_category(current_user):
    data = request.get_json() or {}
    
    if not data.get('name', '').strip():
        return jsonify({'error': 'El nombre de la categoría es requerido'}), 400
    
    category = ProductCategory(
        name=data['name'].strip(),
        description=data.get('description', '').strip() or None,
        color=data.get('color', '').strip() or None,
        icon=data.get('icon', '').strip() or None,
    )
    
    db.session.add(category)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Ya existe una categoría con ese nombre'}), 409
    
    return jsonify(category.to_dict()), 201


@bp.route('/<int:category_id>', methods=['GET'])
@token_required
def get_category(current_user, category_id):
    category = ProductCategory.query.get_or_404(category_id)
    return jsonify(category.to_dict()), 200


@bp.route('/<int:category_id>', methods=['PUT'])
@token_required
@admin_required
def update_category(current_user, category_id):
    category = ProductCategory.query.get_or_404(category_id)
    data = request.get_json() or {}
    
    if 'name' in data:
        if not data['name'].strip():
            return jsonify({'error': 'El nombre no puede estar vacío'}), 400
        category.name = data['name'].strip()
    
    for field in ('description', 'color', 'icon'):
        if field in data:
            val = data[field]
            setattr(category, field, val.strip() if val else None)
    
    if 'is_active' in data:
        category.is_active = bool(data['is_active'])
    
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Ya existe una categoría con ese nombre'}), 409
    
    return jsonify(category.to_dict()), 200


@bp.route('/<int:category_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_category(current_user, category_id):
    category = ProductCategory.query.get_or_404(category_id)
    category.is_active = False
    db.session.commit()
    return jsonify({'message': 'Categoría desactivada correctamente'}), 200
```

- [ ] **Step 2: Registrar blueprint en `backend/app/__init__.py`**

En la línea que importa routes, agregar `product_categories`:

```python
from app.routes import auth, schedules, sales, expenses, reports, employees, shifts, schedule_summary, notifications, coverage, ml_predictions, ml_dashboard, employee_schedule, job_positions, time_tracking, payroll, csv_import, holidays, store_hours, vacation_periods, absence_requests, social_security, employee_documents, fudo_sync, suppliers, product_categories
```

Y luego registrarlo después de `suppliers.bp`:

```python
app.register_blueprint(product_categories.bp)
```

- [ ] **Step 3: Crear `backend/tests/test_product_categories.py`**

```python
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.product_category import ProductCategory
import json


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(email='admin@test.com', role='admin', is_active=True)
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        return user


def get_auth_token(client, email, password):
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    return json.loads(response.data).get('access_token')


def test_create_category(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés', 'description': 'Bebidas calientes', 'color': '#16a34a', 'icon': '☕'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Cafés'
    assert data['is_active'] == True


def test_create_category_missing_name(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/product-categories',
        json={'description': 'Sin nombre'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400


def test_create_category_duplicate_name(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés'},
        headers={'Authorization': f'Bearer {token}'}
    )
    response = client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 409


def test_list_categories(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés'},
        headers={'Authorization': f'Bearer {token}'}
    )
    client.post(
        '/api/v1/product-categories',
        json={'name': 'Panadería'},
        headers={'Authorization': f'Bearer {token}'}
    )
    response = client.get('/api/v1/product-categories', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 2


def test_list_categories_exclude_inactive(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés'},
        headers={'Authorization': f'Bearer {token}'}
    )
    cat_id = json.loads(response.data)['id']
    client.delete(f'/api/v1/product-categories/{cat_id}', headers={'Authorization': f'Bearer {token}'})
    
    response = client.get('/api/v1/product-categories', headers={'Authorization': f'Bearer {token}'})
    data = json.loads(response.data)
    assert data['total'] == 0


def test_get_category(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    create_resp = client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés', 'color': '#16a34a'},
        headers={'Authorization': f'Bearer {token}'}
    )
    cat_id = json.loads(create_resp.data)['id']
    
    response = client.get(f'/api/v1/product-categories/{cat_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Cafés'
    assert data['color'] == '#16a34a'


def test_update_category(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    create_resp = client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés'},
        headers={'Authorization': f'Bearer {token}'}
    )
    cat_id = json.loads(create_resp.data)['id']
    
    response = client.put(
        f'/api/v1/product-categories/{cat_id}',
        json={'name': 'Cafés Premium', 'color': '#fbbf24'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Cafés Premium'
    assert data['color'] == '#fbbf24'


def test_delete_category(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    create_resp = client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés'},
        headers={'Authorization': f'Bearer {token}'}
    )
    cat_id = json.loads(create_resp.data)['id']
    
    response = client.delete(f'/api/v1/product-categories/{cat_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    
    response = client.get(f'/api/v1/product-categories/{cat_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404
```

- [ ] **Step 4: Ejecutar tests**

```bash
cd backend
pytest tests/test_product_categories.py -v
```

Resultado esperado: todos los tests pasan (8 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/product_categories.py \
        backend/app/__init__.py \
        backend/tests/test_product_categories.py
git commit -m "feat: add product_categories blueprint and tests"
```

---

## Task 4: Blueprint products + tests

**Files:**
- Create: `backend/app/routes/products.py`
- Create: `backend/tests/test_products.py`
- Modify: `backend/app/__init__.py`

- [ ] **Step 1: Crear `backend/app/routes/products.py`**

```python
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.product_recipe_item import ProductRecipeItem
from app.models.product_category import ProductCategory
from app.models.supply import Supply
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required
from sqlalchemy.exc import IntegrityError

bp = Blueprint('products', __name__, url_prefix='/api/v1/products')


@bp.route('', methods=['GET'])
@token_required
def list_products(current_user):
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '').strip()
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Product.query
    if not include_inactive:
        query = query.filter(Product.is_active == True)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    paginated = query.order_by(Product.name).paginate(page=page, per_page=per_page, error_out=False)
    products = [p.to_dict() for p in paginated.items]
    
    for p in products:
        variants = ProductVariant.query.filter_by(product_id=p['id'], is_active=True).all()
        p['variants'] = [v.to_dict() for v in variants]

    return jsonify({
        'products': products,
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    }), 200


@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_product(current_user):
    data = request.get_json() or {}

    if not data.get('name', '').strip():
        return jsonify({'error': 'El nombre del producto es requerido'}), 400
    if not data.get('category_id'):
        return jsonify({'error': 'El category_id es requerido'}), 400

    if not ProductCategory.query.get(data['category_id']):
        return jsonify({'error': 'Categoría no encontrada'}), 404

    product = Product(
        name=data['name'].strip(),
        description=data.get('description', '').strip() or None,
        category_id=data['category_id'],
        image_url=data.get('image_url', '').strip() or None,
        has_recipe=bool(data.get('has_recipe', False)),
    )

    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@bp.route('/<int:product_id>', methods=['GET'])
@token_required
def get_product(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    data = product.to_dict()
    
    variants = ProductVariant.query.filter_by(product_id=product_id).all()
    data['variants'] = [v.to_dict() for v in variants]
    
    if product.has_recipe:
        recipe = ProductRecipeItem.query.filter_by(product_id=product_id).all()
        data['recipe'] = [r.to_dict() for r in recipe]
    
    return jsonify(data), 200


@bp.route('/<int:product_id>', methods=['PUT'])
@token_required
@admin_required
def update_product(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}

    if 'name' in data:
        if not data['name'].strip():
            return jsonify({'error': 'El nombre no puede estar vacío'}), 400
        product.name = data['name'].strip()

    if 'category_id' in data:
        if not ProductCategory.query.get(data['category_id']):
            return jsonify({'error': 'Categoría no encontrada'}), 404
        product.category_id = data['category_id']

    for field in ('description', 'image_url'):
        if field in data:
            val = data[field]
            setattr(product, field, val.strip() if val else None)

    if 'has_recipe' in data:
        product.has_recipe = bool(data['has_recipe'])

    if 'is_active' in data:
        product.is_active = bool(data['is_active'])

    db.session.commit()
    return jsonify(product.to_dict()), 200


@bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_product(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = False
    db.session.commit()
    return jsonify({'message': 'Producto desactivado correctamente'}), 200


@bp.route('/<int:product_id>/variants', methods=['GET'])
@token_required
def get_variants(current_user, product_id):
    Product.query.get_or_404(product_id)
    variants = ProductVariant.query.filter_by(product_id=product_id).order_by(ProductVariant.name).all()
    return jsonify({'variants': [v.to_dict() for v in variants], 'total': len(variants)}), 200


@bp.route('/<int:product_id>/variants', methods=['POST'])
@token_required
@admin_required
def create_variant(current_user, product_id):
    Product.query.get_or_404(product_id)
    data = request.get_json() or {}

    if not data.get('name', '').strip():
        return jsonify({'error': 'El nombre de la variante es requerido'}), 400
    if not data.get('price'):
        return jsonify({'error': 'El precio es requerido'}), 400

    variant = ProductVariant(
        product_id=product_id,
        name=data['name'].strip(),
        price=float(data['price']),
        stock_quantity=float(data.get('stock_quantity', 0)),
        min_stock=float(data.get('min_stock', 0)),
    )

    db.session.add(variant)
    db.session.commit()
    return jsonify(variant.to_dict()), 201


@bp.route('/<int:product_id>/variants/<int:variant_id>', methods=['PUT'])
@token_required
@admin_required
def update_variant(current_user, product_id, variant_id):
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first_or_404()
    data = request.get_json() or {}

    if 'name' in data:
        if not data['name'].strip():
            return jsonify({'error': 'El nombre no puede estar vacío'}), 400
        variant.name = data['name'].strip()

    if 'price' in data:
        variant.price = float(data['price'])

    if 'stock_quantity' in data:
        variant.stock_quantity = float(data['stock_quantity'])

    if 'min_stock' in data:
        variant.min_stock = float(data['min_stock'])

    if 'is_active' in data:
        variant.is_active = bool(data['is_active'])

    db.session.commit()
    return jsonify(variant.to_dict()), 200


@bp.route('/<int:product_id>/variants/<int:variant_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_variant(current_user, product_id, variant_id):
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first_or_404()
    variant.is_active = False
    db.session.commit()
    return jsonify({'message': 'Variante desactivada correctamente'}), 200


@bp.route('/<int:product_id>/recipe', methods=['GET'])
@token_required
def get_recipe(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    if not product.has_recipe:
        return jsonify({'recipe': []}), 200

    items = ProductRecipeItem.query.filter_by(product_id=product_id).all()
    return jsonify({'recipe': [i.to_dict() for i in items], 'total': len(items)}), 200


@bp.route('/<int:product_id>/recipe', methods=['PUT'])
@token_required
@admin_required
def update_recipe(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}
    items = data.get('items', [])

    ProductRecipeItem.query.filter_by(product_id=product_id).delete()

    for item in items:
        if not item.get('supply_id') or not item.get('quantity'):
            continue
        
        if not Supply.query.get(item['supply_id']):
            db.session.rollback()
            return jsonify({'error': f"Supply {item['supply_id']} no encontrado"}), 404

        recipe_item = ProductRecipeItem(
            product_id=product_id,
            supply_id=item['supply_id'],
            quantity=float(item['quantity']),
            unit=item.get('unit', ''),
        )
        db.session.add(recipe_item)

    db.session.commit()
    items = ProductRecipeItem.query.filter_by(product_id=product_id).all()
    return jsonify({'recipe': [i.to_dict() for i in items]}), 200


@bp.route('/low-stock', methods=['GET'])
@token_required
def get_low_stock(current_user):
    low_variants = db.session.query(ProductVariant).filter(
        ProductVariant.stock_quantity <= ProductVariant.min_stock,
        ProductVariant.is_active == True
    ).all()

    low_supplies = db.session.query(Supply).filter(
        Supply.stock_quantity <= Supply.min_stock,
        Supply.is_active == True
    ).all()

    return jsonify({
        'variants': [v.to_dict() for v in low_variants],
        'supplies': [s.to_dict() for s in low_supplies],
        'total_variants': len(low_variants),
        'total_supplies': len(low_supplies),
    }), 200


@bp.route('/<int:product_id>/variants/<int:variant_id>/stock', methods=['PUT'])
@token_required
@admin_required
def adjust_stock(current_user, product_id, variant_id):
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first_or_404()
    data = request.get_json() or {}

    if 'stock_quantity' not in data:
        return jsonify({'error': 'stock_quantity es requerido'}), 400

    variant.stock_quantity = float(data['stock_quantity'])
    db.session.commit()
    return jsonify(variant.to_dict()), 200
```

- [ ] **Step 2: Registrar blueprint en `backend/app/__init__.py`**

Agregar `products` a la línea de imports de routes:

```python
from app.routes import auth, schedules, sales, expenses, reports, employees, shifts, schedule_summary, notifications, coverage, ml_predictions, ml_dashboard, employee_schedule, job_positions, time_tracking, payroll, csv_import, holidays, store_hours, vacation_periods, absence_requests, social_security, employee_documents, fudo_sync, suppliers, product_categories, products
```

Y registrarlo después de `product_categories.bp`:

```python
app.register_blueprint(products.bp)
```

- [ ] **Step 3: Crear `backend/tests/test_products.py`**

```python
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.product_category import ProductCategory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.product_recipe_item import ProductRecipeItem
from app.models.supply import Supply
import json


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(email='admin@test.com', role='admin', is_active=True)
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def category(app):
    with app.app_context():
        cat = ProductCategory(name='Cafés', color='#16a34a')
        db.session.add(cat)
        db.session.commit()
        return cat


def get_auth_token(client, email, password):
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    return json.loads(response.data).get('access_token')


def test_create_product(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/products',
        json={'name': 'Café con Leche', 'category_id': category.id, 'has_recipe': False},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Café con Leche'


def test_list_products(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    client.post(
        '/api/v1/products',
        json={'name': 'Café', 'category_id': category.id},
        headers={'Authorization': f'Bearer {token}'}
    )
    response = client.get('/api/v1/products', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 1


def test_create_variant(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Café', 'category_id': category.id},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    response = client.post(
        f'/api/v1/products/{prod_id}/variants',
        json={'name': 'Chico', 'price': 150, 'stock_quantity': 100, 'min_stock': 10},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Chico'
    assert float(data['price']) == 150.0


def test_get_variants(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Café', 'category_id': category.id},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    client.post(
        f'/api/v1/products/{prod_id}/variants',
        json={'name': 'Chico', 'price': 150},
        headers={'Authorization': f'Bearer {token}'}
    )
    client.post(
        f'/api/v1/products/{prod_id}/variants',
        json={'name': 'Grande', 'price': 200},
        headers={'Authorization': f'Bearer {token}'}
    )

    response = client.get(f'/api/v1/products/{prod_id}/variants', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 2


def test_update_variant(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Café', 'category_id': category.id},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    var_resp = client.post(
        f'/api/v1/products/{prod_id}/variants',
        json={'name': 'Chico', 'price': 150},
        headers={'Authorization': f'Bearer {token}'}
    )
    var_id = json.loads(var_resp.data)['id']

    response = client.put(
        f'/api/v1/products/{prod_id}/variants/{var_id}',
        json={'price': 180},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert float(data['price']) == 180.0


def test_update_recipe(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    supply = Supply(name='Leche', unit='litro')
    db.session.add(supply)
    db.session.commit()

    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Café con Leche', 'category_id': category.id, 'has_recipe': True},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    response = client.put(
        f'/api/v1/products/{prod_id}/recipe',
        json={'items': [{'supply_id': supply.id, 'quantity': 0.2, 'unit': 'litro'}]},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['recipe']) == 1


def test_low_stock(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Café', 'category_id': category.id},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    client.post(
        f'/api/v1/products/{prod_id}/variants',
        json={'name': 'Chico', 'price': 150, 'stock_quantity': 5, 'min_stock': 10},
        headers={'Authorization': f'Bearer {token}'}
    )

    response = client.get('/api/v1/products/low-stock', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total_variants'] == 1
```

- [ ] **Step 4: Ejecutar tests**

```bash
cd backend
pytest tests/test_products.py -v
```

Resultado esperado: todos los tests pasan (10 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/products.py \
        backend/app/__init__.py \
        backend/tests/test_products.py
git commit -m "feat: add products blueprint with variants and recipe endpoints"
```

---

## Task 5: Blueprint salons + tests

**Files:**
- Create: `backend/app/routes/salons.py`
- Create: `backend/tests/test_salons.py`
- Modify: `backend/app/__init__.py`

- [ ] **Step 1: Crear `backend/app/routes/salons.py`**

```python
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.salon import Salon
from app.models.mesa import Mesa
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required

bp = Blueprint('salons', __name__, url_prefix='/api/v1/salons')


@bp.route('', methods=['GET'])
@token_required
def list_salons(current_user):
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    
    query = Salon.query
    if not include_inactive:
        query = query.filter(Salon.is_active == True)
    
    salons = query.order_by(Salon.name).all()
    result = []
    for salon in salons:
        data = salon.to_dict()
        mesas = Mesa.query.filter_by(salon_id=salon.id, is_active=True).count()
        data['mesa_count'] = mesas
        result.append(data)
    
    return jsonify({'salons': result, 'total': len(result)}), 200


@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_salon(current_user):
    data = request.get_json() or {}
    
    if not data.get('name', '').strip():
        return jsonify({'error': 'El nombre del salón es requerido'}), 400
    
    salon = Salon(
        name=data['name'].strip(),
        description=data.get('description', '').strip() or None,
    )
    
    db.session.add(salon)
    db.session.commit()
    
    result = salon.to_dict()
    result['mesa_count'] = 0
    return jsonify(result), 201


@bp.route('/<int:salon_id>', methods=['GET'])
@token_required
def get_salon(current_user, salon_id):
    salon = Salon.query.get_or_404(salon_id)
    data = salon.to_dict()
    mesas = Mesa.query.filter_by(salon_id=salon_id).all()
    data['mesas'] = [m.to_dict() for m in mesas]
    data['mesa_count'] = len(mesas)
    return jsonify(data), 200


@bp.route('/<int:salon_id>', methods=['PUT'])
@token_required
@admin_required
def update_salon(current_user, salon_id):
    salon = Salon.query.get_or_404(salon_id)
    data = request.get_json() or {}
    
    if 'name' in data:
        if not data['name'].strip():
            return jsonify({'error': 'El nombre no puede estar vacío'}), 400
        salon.name = data['name'].strip()
    
    if 'description' in data:
        val = data['description']
        salon.description = val.strip() if val else None
    
    if 'is_active' in data:
        salon.is_active = bool(data['is_active'])
    
    db.session.commit()
    
    result = salon.to_dict()
    mesas = Mesa.query.filter_by(salon_id=salon_id, is_active=True).count()
    result['mesa_count'] = mesas
    return jsonify(result), 200


@bp.route('/<int:salon_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_salon(current_user, salon_id):
    salon = Salon.query.get_or_404(salon_id)
    salon.is_active = False
    db.session.commit()
    return jsonify({'message': 'Salón desactivado correctamente'}), 200


@bp.route('/<int:salon_id>/mesas', methods=['GET'])
@token_required
def list_mesas(current_user, salon_id):
    Salon.query.get_or_404(salon_id)
    mesas = Mesa.query.filter_by(salon_id=salon_id).order_by(Mesa.number).all()
    return jsonify({'mesas': [m.to_dict() for m in mesas], 'total': len(mesas)}), 200


@bp.route('/<int:salon_id>/mesas', methods=['POST'])
@token_required
@admin_required
def create_mesa(current_user, salon_id):
    Salon.query.get_or_404(salon_id)
    data = request.get_json() or {}
    
    if not data.get('number'):
        return jsonify({'error': 'El número de mesa es requerido'}), 400
    
    mesa = Mesa(
        salon_id=salon_id,
        number=int(data['number']),
        name=data.get('name', '').strip() or None,
        capacity=data.get('capacity', type=int) or None,
        pos_x=float(data.get('pos_x', 10.0)),
        pos_y=float(data.get('pos_y', 10.0)),
        width=float(data.get('width', 10.0)),
        height=float(data.get('height', 10.0)),
        status=data.get('status', 'libre'),
    )
    
    db.session.add(mesa)
    db.session.commit()
    return jsonify(mesa.to_dict()), 201


@bp.route('/<int:salon_id>/mesas/<int:mesa_id>', methods=['GET'])
@token_required
def get_mesa(current_user, salon_id, mesa_id):
    mesa = Mesa.query.filter_by(id=mesa_id, salon_id=salon_id).first_or_404()
    return jsonify(mesa.to_dict()), 200


@bp.route('/<int:salon_id>/mesas/<int:mesa_id>', methods=['PUT'])
@token_required
@admin_required
def update_mesa(current_user, salon_id, mesa_id):
    mesa = Mesa.query.filter_by(id=mesa_id, salon_id=salon_id).first_or_404()
    data = request.get_json() or {}
    
    if 'number' in data:
        mesa.number = int(data['number'])
    
    for field in ('name', 'status'):
        if field in data:
            val = data[field]
            setattr(mesa, field, val.strip() if val else None)
    
    if 'capacity' in data:
        mesa.capacity = int(data['capacity']) if data['capacity'] else None
    
    for field in ('pos_x', 'pos_y', 'width', 'height'):
        if field in data:
            setattr(mesa, field, float(data[field]))
    
    if 'is_active' in data:
        mesa.is_active = bool(data['is_active'])
    
    db.session.commit()
    return jsonify(mesa.to_dict()), 200


@bp.route('/<int:salon_id>/mesas/<int:mesa_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_mesa(current_user, salon_id, mesa_id):
    mesa = Mesa.query.filter_by(id=mesa_id, salon_id=salon_id).first_or_404()
    mesa.is_active = False
    db.session.commit()
    return jsonify({'message': 'Mesa desactivada correctamente'}), 200
```

- [ ] **Step 2: Registrar blueprint en `backend/app/__init__.py`**

Agregar `salons` a la línea de imports de routes:

```python
from app.routes import auth, schedules, sales, expenses, reports, employees, shifts, schedule_summary, notifications, coverage, ml_predictions, ml_dashboard, employee_schedule, job_positions, time_tracking, payroll, csv_import, holidays, store_hours, vacation_periods, absence_requests, social_security, employee_documents, fudo_sync, suppliers, product_categories, products, salons
```

Y registrarlo después de `products.bp`:

```python
app.register_blueprint(salons.bp)
```

- [ ] **Step 3: Crear `backend/tests/test_salons.py`**

```python
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.salon import Salon
from app.models.mesa import Mesa
import json


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(email='admin@test.com', role='admin', is_active=True)
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        return user


def get_auth_token(client, email, password):
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    return json.loads(response.data).get('access_token')


def test_create_salon(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal', 'description': 'Área principal del café'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Salón Principal'
    assert data['is_active'] == True


def test_list_salons(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    client.post(
        '/api/v1/salons',
        json={'name': 'Terraza'},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    response = client.get('/api/v1/salons', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 2


def test_get_salon(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    create_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(create_resp.data)['id']
    
    response = client.get(f'/api/v1/salons/{salon_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Salón Principal'
    assert data['mesa_count'] == 0


def test_create_mesa(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']
    
    response = client.post(
        f'/api/v1/salons/{salon_id}/mesas',
        json={'number': 1, 'name': 'Mesa 1', 'capacity': 4, 'pos_x': 10.0, 'pos_y': 10.0, 'width': 8.0, 'height': 8.0},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['number'] == 1
    assert data['status'] == 'libre'


def test_list_mesas(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']
    
    client.post(
        f'/api/v1/salons/{salon_id}/mesas',
        json={'number': 1},
        headers={'Authorization': f'Bearer {token}'}
    )
    client.post(
        f'/api/v1/salons/{salon_id}/mesas',
        json={'number': 2},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    response = client.get(f'/api/v1/salons/{salon_id}/mesas', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 2


def test_update_mesa_position(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']
    
    mesa_resp = client.post(
        f'/api/v1/salons/{salon_id}/mesas',
        json={'number': 1, 'pos_x': 10.0, 'pos_y': 10.0},
        headers={'Authorization': f'Bearer {token}'}
    )
    mesa_id = json.loads(mesa_resp.data)['id']
    
    response = client.put(
        f'/api/v1/salons/{salon_id}/mesas/{mesa_id}',
        json={'pos_x': 30.5, 'pos_y': 45.2, 'width': 12.0, 'height': 12.0},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['pos_x'] == 30.5
    assert data['pos_y'] == 45.2
    assert data['width'] == 12.0


def test_update_mesa_status(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']
    
    mesa_resp = client.post(
        f'/api/v1/salons/{salon_id}/mesas',
        json={'number': 1},
        headers={'Authorization': f'Bearer {token}'}
    )
    mesa_id = json.loads(mesa_resp.data)['id']
    
    response = client.put(
        f'/api/v1/salons/{salon_id}/mesas/{mesa_id}',
        json={'status': 'ocupada'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ocupada'


def test_delete_mesa(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']
    
    mesa_resp = client.post(
        f'/api/v1/salons/{salon_id}/mesas',
        json={'number': 1},
        headers={'Authorization': f'Bearer {token}'}
    )
    mesa_id = json.loads(mesa_resp.data)['id']
    
    response = client.delete(f'/api/v1/salons/{salon_id}/mesas/{mesa_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    
    response = client.get(f'/api/v1/salons/{salon_id}/mesas/{mesa_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404
```

- [ ] **Step 4: Ejecutar tests**

```bash
cd backend
pytest tests/test_salons.py -v
```

Resultado esperado: todos los tests pasan (8 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/salons.py \
        backend/app/__init__.py \
        backend/tests/test_salons.py
git commit -m "feat: add salons blueprint with mesas layout endpoints"
```

---

## Task 6: Extensiones sales + stock_service + tests

**Files:**
- Create: `backend/app/services/stock_service.py`
- Modify: `backend/app/routes/sales.py` (agregar nuevos endpoints)
- Create: `backend/tests/test_sales_products.py`

- [ ] **Step 1: Crear `backend/app/services/stock_service.py`**

```python
from app.extensions import db
from app.models.product_variant import ProductVariant
from app.models.product_recipe_item import ProductRecipeItem
from app.models.supply import Supply


def deduct_stock_for_sale(sale_items):
    """
    Descuenta stock para una venta.
    sale_items: lista de {'product_variant_id': int, 'quantity': int}
    
    Lógica:
    - Si producto.has_recipe = False: descuenta de ProductVariant.stock_quantity
    - Si producto.has_recipe = True: descuenta de Supply según receta
    
    Levanta excepción si hay stock insuficiente o variante no existe.
    """
    for item in sale_items:
        variant = ProductVariant.query.get(item['product_variant_id'])
        if not variant:
            raise ValueError(f"ProductVariant {item['product_variant_id']} no encontrado")
        
        product = variant.product
        quantity = item['quantity']
        
        if not product.has_recipe:
            if float(variant.stock_quantity) < quantity:
                raise ValueError(f"Stock insuficiente para {product.name} - {variant.name}")
            variant.stock_quantity = float(variant.stock_quantity) - quantity
        else:
            recipe_items = ProductRecipeItem.query.filter_by(product_id=product.id).all()
            for recipe_item in recipe_items:
                supply = recipe_item.supply
                needed = float(recipe_item.quantity) * quantity
                if float(supply.stock_quantity) < needed:
                    raise ValueError(f"Stock insuficiente de {supply.name}")
                supply.stock_quantity = float(supply.stock_quantity) - needed
    
    db.session.flush()
```

- [ ] **Step 2: Extender `backend/app/routes/sales.py`**

Agregar al inicio (después de los imports existentes):

```python
from app.models.product_variant import ProductVariant
from app.models.sale_item import SaleItem
from app.services.stock_service import deduct_stock_for_sale
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import func
```

Y agregar estos endpoints antes del último endpoint:

```python
@bp.route('', methods=['POST'])
@token_required
def create_sale(current_user):
    """
    Crear una venta nueva con items.
    Body: {
      "items": [{"product_variant_id": int, "quantity": int}, ...],
      "mesa_id": int (opcional),
      "medio_pago": str (default: "Efectivo")
    }
    """
    data = request.get_json() or {}
    items = data.get('items', [])
    mesa_id = data.get('mesa_id')
    medio_pago = data.get('medio_pago', 'Efectivo')
    
    if not items:
        return jsonify({'error': 'Al menos un item es requerido'}), 400
    
    try:
        deduct_stock_for_sale(items)
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    
    sale = Sale(
        fecha=date.today(),
        creacion=datetime.utcnow(),
        medio_pago=medio_pago,
        source='galia',
        mesa_id=mesa_id,
        total=Decimal(0),
        estado='En curso',
        tipo_venta='Local',
    )
    
    total = Decimal(0)
    for item in items:
        variant = ProductVariant.query.get(item['product_variant_id'])
        quantity = item['quantity']
        unit_price = variant.price
        subtotal = Decimal(str(unit_price)) * quantity
        total += subtotal
        
        sale_item = SaleItem(
            sale=sale,
            product_variant_id=variant.id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
        )
        db.session.add(sale_item)
    
    sale.total = total
    db.session.add(sale)
    db.session.commit()
    
    return jsonify(sale.to_dict()), 201


@bp.route('/<int:sale_id>', methods=['GET'])
@token_required
def get_sale(current_user, sale_id):
    """Obtener detalle de venta con items"""
    sale = Sale.query.get_or_404(sale_id)
    data = sale.to_dict()
    items = SaleItem.query.filter_by(sale_id=sale_id).all()
    data['items'] = [i.to_dict() for i in items]
    return jsonify(data), 200


@bp.route('/daily-summary', methods=['GET'])
@token_required
def get_daily_summary(current_user):
    """Stats del día: total vendido, cantidad de ventas, top productos"""
    today = date.today()
    
    sales = Sale.query.filter(
        Sale.fecha == today,
        Sale.source == 'galia'
    ).all()
    
    total_vendido = sum(float(s.total) for s in sales)
    cantidad_ventas = len(sales)
    
    top_products = db.session.query(
        ProductVariant.id,
        ProductVariant.name,
        func.count(SaleItem.id).label('cantidad'),
        func.sum(SaleItem.subtotal).label('total')
    ).join(SaleItem).join(Sale).filter(
        Sale.fecha == today,
        Sale.source == 'galia'
    ).group_by(ProductVariant.id, ProductVariant.name).order_by(
        func.sum(SaleItem.subtotal).desc()
    ).limit(5).all()
    
    top_list = []
    for variant_id, name, cantidad, total in top_products:
        top_list.append({
            'product_variant_id': variant_id,
            'name': name,
            'quantity': cantidad,
            'total': float(total) if total else 0,
        })
    
    low_stock = db.session.query(ProductVariant).filter(
        ProductVariant.stock_quantity <= ProductVariant.min_stock,
        ProductVariant.is_active == True
    ).count()
    
    return jsonify({
        'total_vendido': total_vendido,
        'cantidad_ventas': cantidad_ventas,
        'top_products': top_list,
        'bajo_stock_count': low_stock,
    }), 200


@bp.route('/top-products', methods=['GET'])
@token_required
def get_top_products(current_user):
    """Ranking de productos más vendidos con filtro de fecha"""
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    limit = request.args.get('limit', 10, type=int)
    
    query = db.session.query(
        ProductVariant.id,
        ProductVariant.name,
        func.count(SaleItem.id).label('cantidad'),
        func.sum(SaleItem.subtotal).label('total')
    ).join(SaleItem).join(Sale).filter(Sale.source == 'galia')
    
    if fecha_desde:
        try:
            desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            query = query.filter(Sale.fecha >= desde)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            query = query.filter(Sale.fecha <= hasta)
        except ValueError:
            pass
    
    results = query.group_by(ProductVariant.id, ProductVariant.name).order_by(
        func.sum(SaleItem.subtotal).desc()
    ).limit(limit).all()
    
    top_list = []
    for variant_id, name, cantidad, total in results:
        top_list.append({
            'product_variant_id': variant_id,
            'name': name,
            'quantity': cantidad,
            'total': float(total) if total else 0,
        })
    
    return jsonify({'top_products': top_list}), 200
```

- [ ] **Step 3: Verificar que los imports funcionan**

```bash
cd backend
source venv/bin/activate
python -c "
from app import create_app
from app.routes import sales
from app.services.stock_service import deduct_stock_for_sale
from app.models.sale_item import SaleItem
print('OK - sales extended imports work')
"
```

Resultado esperado: `OK - sales extended imports work`

- [ ] **Step 4: Crear `backend/tests/test_sales_products.py`**

```python
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.product_category import ProductCategory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.product_recipe_item import ProductRecipeItem
from app.models.supply import Supply
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.salon import Salon
from app.models.mesa import Mesa
from datetime import date
import json


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(email='admin@test.com', role='admin', is_active=True)
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def category(app):
    with app.app_context():
        cat = ProductCategory(name='Cafés')
        db.session.add(cat)
        db.session.commit()
        return cat


@pytest.fixture
def product_with_variant(app, category):
    with app.app_context():
        prod = Product(name='Café', category_id=category.id, has_recipe=False)
        db.session.add(prod)
        db.session.flush()
        
        variant = ProductVariant(
            product_id=prod.id,
            name='Chico',
            price=150.0,
            stock_quantity=100,
            min_stock=10
        )
        db.session.add(variant)
        db.session.commit()
        return prod, variant


@pytest.fixture
def salon(app):
    with app.app_context():
        s = Salon(name='Salón Principal')
        db.session.add(s)
        db.session.flush()
        
        m = Mesa(salon_id=s.id, number=1)
        db.session.add(m)
        db.session.commit()
        return s, m


def get_auth_token(client, email, password):
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    return json.loads(response.data).get('access_token')


def test_create_sale_simple(client, admin_user, product_with_variant):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    prod, variant = product_with_variant
    
    response = client.post(
        '/api/v1/sales',
        json={
            'items': [{'product_variant_id': variant.id, 'quantity': 2}],
            'medio_pago': 'Efectivo'
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['source'] == 'galia'
    assert float(data['total']) == 300.0


def test_create_sale_with_mesa(client, admin_user, product_with_variant, salon):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    prod, variant = product_with_variant
    s, m = salon
    
    response = client.post(
        '/api/v1/sales',
        json={
            'items': [{'product_variant_id': variant.id, 'quantity': 1}],
            'mesa_id': m.id,
            'medio_pago': 'Débito'
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['mesa_id'] == m.id


def test_create_sale_deducts_stock(client, admin_user, product_with_variant):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    prod, variant = product_with_variant
    
    initial_stock = float(variant.stock_quantity)
    
    client.post(
        '/api/v1/sales',
        json={'items': [{'product_variant_id': variant.id, 'quantity': 5}]},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    db.session.refresh(variant)
    assert float(variant.stock_quantity) == initial_stock - 5


def test_create_sale_insufficient_stock(client, admin_user, product_with_variant):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    prod, variant = product_with_variant
    
    response = client.post(
        '/api/v1/sales',
        json={'items': [{'product_variant_id': variant.id, 'quantity': 200}]},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400


def test_get_sale_with_items(client, admin_user, product_with_variant):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    prod, variant = product_with_variant
    
    sale_resp = client.post(
        '/api/v1/sales',
        json={'items': [{'product_variant_id': variant.id, 'quantity': 2}]},
        headers={'Authorization': f'Bearer {token}'}
    )
    sale_id = json.loads(sale_resp.data)['id']
    
    response = client.get(f'/api/v1/sales/{sale_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['items']) == 1
    assert data['items'][0]['quantity'] == 2


def test_daily_summary(client, admin_user, product_with_variant):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    prod, variant = product_with_variant
    
    client.post(
        '/api/v1/sales',
        json={'items': [{'product_variant_id': variant.id, 'quantity': 2}]},
        headers={'Authorization': f'Bearer {token}'}
    )
    client.post(
        '/api/v1/sales',
        json={'items': [{'product_variant_id': variant.id, 'quantity': 3}]},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    response = client.get('/api/v1/sales/daily-summary', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['cantidad_ventas'] == 2
    assert data['total_vendido'] == 750.0


def test_top_products(client, admin_user, product_with_variant):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    prod, variant = product_with_variant
    
    client.post(
        '/api/v1/sales',
        json={'items': [{'product_variant_id': variant.id, 'quantity': 5}]},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    response = client.get('/api/v1/sales/top-products', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['top_products']) >= 1


def test_recipe_stock_deduction(app, admin_user, client):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    
    with app.app_context():
        cat = ProductCategory(name='Bebidas')
        db.session.add(cat)
        db.session.flush()
        
        prod = Product(name='Cappuccino', category_id=cat.id, has_recipe=True)
        db.session.add(prod)
        db.session.flush()
        
        supply = Supply(name='Leche', unit='litro', stock_quantity=50, min_stock=5)
        db.session.add(supply)
        db.session.flush()
        
        recipe = ProductRecipeItem(product_id=prod.id, supply_id=supply.id, quantity=0.2, unit='litro')
        db.session.add(recipe)
        db.session.flush()
        
        variant = ProductVariant(product_id=prod.id, name='Grande', price=200, stock_quantity=0)
        db.session.add(variant)
        db.session.commit()
    
    response = client.post(
        '/api/v1/sales',
        json={'items': [{'product_variant_id': variant.id, 'quantity': 5}]},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    
    db.session.refresh(supply)
    assert float(supply.stock_quantity) == 50 - (0.2 * 5)
```

- [ ] **Step 5: Ejecutar tests**

```bash
cd backend
pytest tests/test_sales_products.py -v
```

Resultado esperado: todos los tests pasan (10 tests).

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/stock_service.py \
        backend/app/routes/sales.py \
        backend/tests/test_sales_products.py
git commit -m "feat: add sales endpoints with stock deduction and daily summary"
```

---

## Task 7: Servicios JS + Sidebar + rutas App.jsx

**Files:**
- Create: `frontend/src/services/productsService.js`
- Create: `frontend/src/services/productCategoriesService.js`
- Create: `frontend/src/services/salonsService.js`
- Create: `frontend/src/services/salesService.js` (o extender si existe)
- Modify: `frontend/src/components/layout/Sidebar.jsx`
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Crear `frontend/src/services/productsService.js`**

```javascript
import api from './api'

const productsService = {
  async getProducts(params = {}) {
    const response = await api.get('/products', { params })
    return response.data
  },

  async getProduct(id) {
    const response = await api.get(`/products/${id}`)
    return response.data
  },

  async createProduct(data) {
    const response = await api.post('/products', data)
    return response.data
  },

  async updateProduct(id, data) {
    const response = await api.put(`/products/${id}`, data)
    return response.data
  },

  async deleteProduct(id) {
    const response = await api.delete(`/products/${id}`)
    return response.data
  },

  async getVariants(productId) {
    const response = await api.get(`/products/${productId}/variants`)
    return response.data
  },

  async createVariant(productId, data) {
    const response = await api.post(`/products/${productId}/variants`, data)
    return response.data
  },

  async updateVariant(productId, variantId, data) {
    const response = await api.put(`/products/${productId}/variants/${variantId}`, data)
    return response.data
  },

  async deleteVariant(productId, variantId) {
    const response = await api.delete(`/products/${productId}/variants/${variantId}`)
    return response.data
  },

  async getRecipe(productId) {
    const response = await api.get(`/products/${productId}/recipe`)
    return response.data
  },

  async saveRecipe(productId, items) {
    const response = await api.put(`/products/${productId}/recipe`, { items })
    return response.data
  },

  async getLowStock() {
    const response = await api.get('/products/low-stock')
    return response.data
  },

  async adjustStock(productId, variantId, stockQuantity) {
    const response = await api.put(
      `/products/${productId}/variants/${variantId}/stock`,
      { stock_quantity: stockQuantity }
    )
    return response.data
  },
}

export default productsService
```

- [ ] **Step 2: Crear `frontend/src/services/productCategoriesService.js`**

```javascript
import api from './api'

const productCategoriesService = {
  async getCategories(params = {}) {
    const response = await api.get('/product-categories', { params })
    return response.data
  },

  async getCategory(id) {
    const response = await api.get(`/product-categories/${id}`)
    return response.data
  },

  async createCategory(data) {
    const response = await api.post('/product-categories', data)
    return response.data
  },

  async updateCategory(id, data) {
    const response = await api.put(`/product-categories/${id}`, data)
    return response.data
  },

  async deleteCategory(id) {
    const response = await api.delete(`/product-categories/${id}`)
    return response.data
  },
}

export default productCategoriesService
```

- [ ] **Step 3: Crear `frontend/src/services/salonsService.js`**

```javascript
import api from './api'

const salonsService = {
  async getSalons(params = {}) {
    const response = await api.get('/salons', { params })
    return response.data
  },

  async getSalon(id) {
    const response = await api.get(`/salons/${id}`)
    return response.data
  },

  async createSalon(data) {
    const response = await api.post('/salons', data)
    return response.data
  },

  async updateSalon(id, data) {
    const response = await api.put(`/salons/${id}`, data)
    return response.data
  },

  async deleteSalon(id) {
    const response = await api.delete(`/salons/${id}`)
    return response.data
  },

  async getMesas(salonId) {
    const response = await api.get(`/salons/${salonId}/mesas`)
    return response.data
  },

  async getMesa(salonId, mesaId) {
    const response = await api.get(`/salons/${salonId}/mesas/${mesaId}`)
    return response.data
  },

  async createMesa(salonId, data) {
    const response = await api.post(`/salons/${salonId}/mesas`, data)
    return response.data
  },

  async updateMesa(salonId, mesaId, data) {
    const response = await api.put(`/salons/${salonId}/mesas/${mesaId}`, data)
    return response.data
  },

  async deleteMesa(salonId, mesaId) {
    const response = await api.delete(`/salons/${salonId}/mesas/${mesaId}`)
    return response.data
  },
}

export default salonsService
```

- [ ] **Step 4: Crear `frontend/src/services/salesService.js`**

```javascript
import api from './api'

const salesService = {
  async getSales(params = {}) {
    const response = await api.get('/sales', { params })
    return response.data
  },

  async getSale(id) {
    const response = await api.get(`/sales/${id}`)
    return response.data
  },

  async createSale(items, mesaId = null, medioPago = 'Efectivo') {
    const response = await api.post('/sales', {
      items,
      mesa_id: mesaId,
      medio_pago: medioPago,
    })
    return response.data
  },

  async getDailySummary() {
    const response = await api.get('/sales/daily-summary')
    return response.data
  },

  async getTopProducts(params = {}) {
    const response = await api.get('/sales/top-products', { params })
    return response.data
  },
}

export default salesService
```

- [ ] **Step 5: Modificar `frontend/src/components/layout/Sidebar.jsx`**

Buscar el array `navGroups` y agregar un nuevo grupo antes del cierre del array:

```javascript
{
  id: 'menu',
  label: 'Menú ✨',
  icon: ShoppingCart,
  activeClass: 'text-green-700 bg-green-50 border-green-200',
  headerClass: 'text-green-700 bg-green-50',
  items: [
    { to: '/pos', icon: ShoppingCart, label: 'Caja (POS)' },
    { to: '/products', icon: UtensilsCrossed, label: 'Productos' },
    { to: '/product-categories', icon: Tag, label: 'Categorías' },
    { to: '/stock', icon: Package, label: 'Stock' },
  ],
},
```

Agregar los imports necesarios al inicio (si no existen):
```javascript
import { ShoppingCart, UtensilsCrossed, Tag, Package } from 'lucide-react'
```

- [ ] **Step 6: Modificar `frontend/src/App.jsx`**

Agregar los imports de las páginas que crearemos después (por ahora dejaremos placeholder):

```javascript
// Agregar al inicio con los otros imports:
import Pos from './pages/Pos'
import ProductCategories from './pages/ProductCategories'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import Stock from './pages/Stock'
```

Agregar las rutas en el `<Routes>` (antes del `</Routes>`):

```javascript
<Route path="/pos" element={<Pos />} />
<Route path="/products" element={<Products />} />
<Route path="/products/:id" element={<ProductDetail />} />
<Route path="/product-categories" element={<ProductCategories />} />
<Route path="/stock" element={<Stock />} />
```

- [ ] **Step 7: Verificar que los imports funcionan**

```bash
cd frontend
npm run dev
```

Abrir http://localhost:5173 en el navegador. La app debe cargar sin errores. En la consola del navegador no debe haber errores de imports.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/services/productsService.js \
        frontend/src/services/productCategoriesService.js \
        frontend/src/services/salonsService.js \
        frontend/src/services/salesService.js \
        frontend/src/components/layout/Sidebar.jsx \
        frontend/src/App.jsx
git commit -m "feat: add product services and Menu sidebar group with routes"
```

---

## Task 8: Página /product-categories

**Files:**
- Create: `frontend/src/pages/ProductCategories.jsx`

- [ ] **Step 1: Crear `frontend/src/pages/ProductCategories.jsx`**

```javascript
import { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, Save, X } from 'lucide-react'
import productCategoriesService from '../services/productCategoriesService'

const ProductCategories = () => {
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingCategory, setEditingCategory] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    color: '#16a34a',
    icon: '☕',
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchCategories()
  }, [])

  const fetchCategories = async () => {
    setLoading(true)
    try {
      const response = await productCategoriesService.getCategories({ include_inactive: false })
      setCategories(response.categories || [])
    } catch (error) {
      console.error('Error fetching categories:', error)
      setError('Error al cargar las categorías')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenModal = (category = null) => {
    if (category) {
      setEditingCategory(category)
      setFormData({
        name: category.name,
        description: category.description || '',
        color: category.color || '#16a34a',
        icon: category.icon || '☕',
      })
    } else {
      setEditingCategory(null)
      setFormData({
        name: '',
        description: '',
        color: '#16a34a',
        icon: '☕',
      })
    }
    setError('')
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingCategory(null)
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)

    try {
      if (editingCategory) {
        await productCategoriesService.updateCategory(editingCategory.id, formData)
      } else {
        await productCategoriesService.createCategory(formData)
      }
      handleCloseModal()
      fetchCategories()
    } catch (error) {
      setError(error.response?.data?.error || 'Error al guardar la categoría')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if (window.confirm('¿Desactivar esta categoría?')) {
      try {
        await productCategoriesService.deleteCategory(id)
        fetchCategories()
      } catch (error) {
        setError('Error al desactivar la categoría')
      }
    }
  }

  if (loading) {
    return <div className="p-4">Cargando categorías...</div>
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Categorías de Productos</h1>
        <button
          onClick={() => handleOpenModal()}
          className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
        >
          <Plus size={20} /> Nueva Categoría
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {categories.map((category) => (
          <div
            key={category.id}
            className="border rounded-lg p-4 hover:shadow-lg transition"
            style={{ borderLeftColor: category.color || '#ccc', borderLeftWidth: '4px' }}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-3xl">{category.icon || '📦'}</span>
                <h3 className="font-bold text-lg">{category.name}</h3>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleOpenModal(category)}
                  className="p-1 hover:bg-blue-50 rounded text-blue-600"
                >
                  <Edit2 size={18} />
                </button>
                <button
                  onClick={() => handleDelete(category.id)}
                  className="p-1 hover:bg-red-50 rounded text-red-600"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
            {category.description && (
              <p className="text-sm text-gray-600 mb-2">{category.description}</p>
            )}
            <div className="flex items-center gap-2">
              <div
                className="w-6 h-6 rounded border"
                style={{ backgroundColor: category.color || '#ccc' }}
              />
              <span className="text-xs text-gray-500">{category.color}</span>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">
                {editingCategory ? 'Editar Categoría' : 'Nueva Categoría'}
              </h2>
              <button onClick={handleCloseModal} className="text-gray-500 hover:text-gray-700">
                <X size={24} />
              </button>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded mb-4 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Nombre *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="Ej: Cafés"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Descripción</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="Opcional"
                  rows="2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Color</label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={formData.color}
                    onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                    className="w-12 h-10 border rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={formData.color}
                    onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                    className="flex-1 border rounded px-3 py-2 font-mono text-sm"
                    placeholder="#16a34a"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Ícono (emoji)</label>
                <input
                  type="text"
                  value={formData.icon}
                  onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500 text-2xl"
                  placeholder="☕"
                  maxLength="2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Puedes pegar cualquier emoji aquí
                </p>
              </div>

              <div className="flex gap-2 pt-4">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex-1 border border-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={saving || !formData.name}
                  className="flex-1 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:bg-gray-400 flex items-center justify-center gap-2"
                >
                  <Save size={18} />
                  {saving ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProductCategories
```

- [ ] **Step 2: Reemplazar import placeholder en `frontend/src/App.jsx`**

Cambiar:
```javascript
import ProductCategories from './pages/ProductCategories'
```

Por:
```javascript
import ProductCategories from './pages/ProductCategories'
```

(Ya debería estar así después de Task 7)

- [ ] **Step 3: Probar en el navegador**

```bash
cd frontend
npm run dev
```

Ir a http://localhost:5173/product-categories

Verificar:
- La página carga
- Botón "Nueva Categoría" funciona
- Modal se abre/cierra correctamente
- Se pueden crear categorías
- El color picker funciona
- Se pueden editar categorías
- Se pueden desactivar (delete) categorías
- Las categorías aparecen en la grilla

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/ProductCategories.jsx
git commit -m "feat: add ProductCategories page with create/edit/delete"
```

---

## Task 9: Página /products (lista)

**Files:**
- Create: `frontend/src/pages/Products.jsx`

- [ ] **Step 1: Crear `frontend/src/pages/Products.jsx`**

```javascript
import { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, Search } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import productsService from '../services/productsService'
import productCategoriesService from '../services/productCategoriesService'

const Products = () => {
  const navigate = useNavigate()
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchCategories()
  }, [])

  useEffect(() => {
    fetchProducts()
  }, [page, search, categoryFilter])

  const fetchCategories = async () => {
    try {
      const response = await productCategoriesService.getCategories({
        include_inactive: false,
      })
      setCategories(response.categories || [])
    } catch (error) {
      console.error('Error fetching categories:', error)
    }
  }

  const fetchProducts = async () => {
    setLoading(true)
    try {
      const params = {
        page,
        per_page: 20,
        search: search.trim(),
      }
      if (categoryFilter) {
        params.category_id = categoryFilter
      }

      const response = await productsService.getProducts(params)
      setProducts(response.products || [])
      setTotalPages(response.pages || 1)
      setError('')
    } catch (error) {
      console.error('Error fetching products:', error)
      setError('Error al cargar los productos')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (window.confirm('¿Desactivar este producto?')) {
      try {
        await productsService.deleteProduct(id)
        fetchProducts()
      } catch (error) {
        setError('Error al desactivar el producto')
      }
    }
  }

  const handleSearch = (e) => {
    setSearch(e.target.value)
    setPage(1)
  }

  const handleCategoryFilter = (e) => {
    setCategoryFilter(e.target.value)
    setPage(1)
  }

  if (loading && products.length === 0) {
    return <div className="p-4">Cargando productos...</div>
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Productos</h1>
        <button
          onClick={() => navigate('/product-detail')}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          <Plus size={20} /> Nuevo Producto
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <div className="flex gap-4 mb-4">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar por nombre..."
              value={search}
              onChange={handleSearch}
              className="w-full border rounded px-3 py-2 pl-10 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={categoryFilter}
            onChange={handleCategoryFilter}
            className="border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          >
            <option value="">Todas las categorías</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.icon} {cat.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-6 py-3 font-medium text-sm text-gray-700">
                Producto
              </th>
              <th className="text-left px-6 py-3 font-medium text-sm text-gray-700">
                Categoría
              </th>
              <th className="text-left px-6 py-3 font-medium text-sm text-gray-700">
                Variantes
              </th>
              <th className="text-left px-6 py-3 font-medium text-sm text-gray-700">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {products.length === 0 ? (
              <tr>
                <td colSpan="4" className="px-6 py-4 text-center text-gray-500">
                  No hay productos
                </td>
              </tr>
            ) : (
              products.map((product) => (
                <tr key={product.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <button
                      onClick={() => navigate(`/products/${product.id}`)}
                      className="text-blue-600 hover:underline font-medium"
                    >
                      {product.name}
                    </button>
                    {product.has_recipe && (
                      <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                        Receta
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {product.category_icon && (
                      <span className="mr-2">{product.category_icon}</span>
                    )}
                    {product.category_name || '-'}
                  </td>
                  <td className="px-6 py-4">
                    {product.variants && product.variants.length > 0 ? (
                      <div className="flex gap-1 flex-wrap">
                        {product.variants.map((variant) => (
                          <span
                            key={variant.id}
                            className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
                          >
                            {variant.name}: ${variant.price}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => navigate(`/products/${product.id}`)}
                        className="p-1 hover:bg-blue-50 rounded text-blue-600"
                        title="Editar"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => handleDelete(product.id)}
                        className="p-1 hover:bg-red-50 rounded text-red-600"
                        title="Desactivar"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-3 py-1 border rounded hover:bg-gray-50 disabled:text-gray-400"
          >
            Anterior
          </button>
          <span className="px-3 py-1">
            Página {page} de {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="px-3 py-1 border rounded hover:bg-gray-50 disabled:text-gray-400"
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  )
}

export default Products
```

- [ ] **Step 2: Probar en el navegador**

```bash
cd frontend
npm run dev
```

Ir a http://localhost:5173/products

Verificar:
- Página carga
- Tabla muestra productos (vacía es OK si no hay)
- Filtro de búsqueda funciona
- Filtro de categoría funciona
- Botón "Nuevo Producto" navega (aún sin implementar)
- Botones editar/eliminar funcionan (eliminar desactiva)
- Paginación funciona si hay múltiples páginas

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Products.jsx
git commit -m "feat: add Products list page with filters and pagination"
```

---

## Task 10: Página /products/:id (detalle + 4 tabs)

**Files:**
- Create: `frontend/src/pages/ProductDetail.jsx`

- [ ] **Step 1: Crear `frontend/src/pages/ProductDetail.jsx`**

```javascript
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Save, X, Plus, Trash2, ArrowLeft } from 'lucide-react'
import productsService from '../services/productsService'
import productCategoriesService from '../services/productCategoriesService'

const ProductDetail = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const isNew = id === undefined || id === 'new'

  const [product, setProduct] = useState(null)
  const [categories, setCategories] = useState([])
  const [supplies, setSupplies] = useState([])
  const [loading, setLoading] = useState(!isNew)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('info')

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category_id: '',
    image_url: '',
    has_recipe: false,
  })

  const [variants, setVariants] = useState([])
  const [recipe, setRecipe] = useState([])
  const [newVariantForm, setNewVariantForm] = useState({
    name: '',
    price: '',
    stock_quantity: '',
    min_stock: '',
  })
  const [newRecipeForm, setNewRecipeForm] = useState({
    supply_id: '',
    quantity: '',
    unit: '',
  })

  useEffect(() => {
    fetchCategories()
    if (!isNew) {
      fetchProduct()
    }
  }, [])

  const fetchCategories = async () => {
    try {
      const response = await productCategoriesService.getCategories({
        include_inactive: false,
      })
      setCategories(response.categories || [])
    } catch (error) {
      console.error('Error fetching categories:', error)
    }
  }

  const fetchProduct = async () => {
    try {
      const response = await productsService.getProduct(id)
      setProduct(response)
      setFormData({
        name: response.name,
        description: response.description || '',
        category_id: response.category_id,
        image_url: response.image_url || '',
        has_recipe: response.has_recipe,
      })
      setVariants(response.variants || [])
      setRecipe(response.recipe || [])
      setError('')
    } catch (error) {
      console.error('Error fetching product:', error)
      setError('Error al cargar el producto')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveProduct = async () => {
    if (!formData.name.trim() || !formData.category_id) {
      setError('Nombre y categoría son requeridos')
      return
    }

    setSaving(true)
    try {
      if (isNew) {
        const newProduct = await productsService.createProduct(formData)
        navigate(`/products/${newProduct.id}`)
      } else {
        await productsService.updateProduct(id, formData)
        fetchProduct()
      }
      setError('')
    } catch (error) {
      setError(error.response?.data?.error || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const handleAddVariant = async () => {
    if (!newVariantForm.name.trim() || !newVariantForm.price) {
      setError('Nombre y precio son requeridos')
      return
    }

    try {
      const newVariant = await productsService.createVariant(id || product.id, {
        name: newVariantForm.name,
        price: parseFloat(newVariantForm.price),
        stock_quantity: parseFloat(newVariantForm.stock_quantity || 0),
        min_stock: parseFloat(newVariantForm.min_stock || 0),
      })
      setVariants([...variants, newVariant])
      setNewVariantForm({ name: '', price: '', stock_quantity: '', min_stock: '' })
      setError('')
    } catch (error) {
      setError(error.response?.data?.error || 'Error al crear variante')
    }
  }

  const handleDeleteVariant = async (variantId) => {
    if (window.confirm('¿Desactivar esta variante?')) {
      try {
        await productsService.deleteVariant(id || product.id, variantId)
        setVariants(variants.filter((v) => v.id !== variantId))
        setError('')
      } catch (error) {
        setError('Error al desactivar variante')
      }
    }
  }

  const handleUpdateVariant = async (variantId, field, value) => {
    try {
      const variant = variants.find((v) => v.id === variantId)
      const updated = { ...variant, [field]: value }
      await productsService.updateVariant(id || product.id, variantId, updated)
      setVariants(
        variants.map((v) => (v.id === variantId ? { ...v, [field]: value } : v))
      )
    } catch (error) {
      setError('Error al actualizar variante')
    }
  }

  const handleAddRecipeItem = async () => {
    if (!newRecipeForm.supply_id || !newRecipeForm.quantity) {
      setError('Insumo y cantidad son requeridos')
      return
    }

    try {
      const items = [
        ...recipe,
        {
          supply_id: parseInt(newRecipeForm.supply_id),
          quantity: parseFloat(newRecipeForm.quantity),
          unit: newRecipeForm.unit,
        },
      ]
      await productsService.saveRecipe(id || product.id, items)
      setRecipe(items)
      setNewRecipeForm({ supply_id: '', quantity: '', unit: '' })
      setError('')
    } catch (error) {
      setError(error.response?.data?.error || 'Error al agregar a receta')
    }
  }

  const handleDeleteRecipeItem = async (index) => {
    try {
      const items = recipe.filter((_, i) => i !== index)
      await productsService.saveRecipe(id || product.id, items)
      setRecipe(items)
    } catch (error) {
      setError('Error al eliminar de receta')
    }
  }

  if (loading) {
    return <div className="p-4">Cargando...</div>
  }

  return (
    <div className="p-6">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/products')}
          className="p-2 hover:bg-gray-100 rounded"
        >
          <ArrowLeft size={24} />
        </button>
        <h1 className="text-3xl font-bold">
          {isNew ? 'Nuevo Producto' : product?.name}
        </h1>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="border-b flex">
          {['info', 'variantes', 'receta', 'historial'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 font-medium ${
                activeTab === tab
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab === 'info' && 'Información'}
              {tab === 'variantes' && 'Variantes'}
              {tab === 'receta' && 'Receta'}
              {tab === 'historial' && 'Historial'}
            </button>
          ))}
        </div>

        <div className="p-6">
          {activeTab === 'info' && (
            <div className="space-y-4 max-w-2xl">
              <div>
                <label className="block text-sm font-medium mb-1">Nombre *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Descripción</label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  rows="3"
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Categoría *</label>
                <select
                  value={formData.category_id}
                  onChange={(e) =>
                    setFormData({ ...formData, category_id: parseInt(e.target.value) })
                  }
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Seleccionar categoría</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon} {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">URL de Imagen</label>
                <input
                  type="text"
                  value={formData.image_url}
                  onChange={(e) =>
                    setFormData({ ...formData, image_url: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://..."
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="has_recipe"
                  checked={formData.has_recipe}
                  onChange={(e) =>
                    setFormData({ ...formData, has_recipe: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <label htmlFor="has_recipe" className="font-medium">
                  Este producto tiene receta (compuesto de insumos)
                </label>
              </div>

              <div className="flex gap-2 pt-4">
                <button
                  onClick={handleSaveProduct}
                  disabled={saving}
                  className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
                >
                  <Save size={18} />
                  {saving ? 'Guardando...' : 'Guardar'}
                </button>
                <button
                  onClick={() => navigate('/products')}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}

          {activeTab === 'variantes' && product && (
            <div>
              <table className="w-full mb-6 border-collapse">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="text-left px-4 py-2 text-sm font-medium">Nombre</th>
                    <th className="text-left px-4 py-2 text-sm font-medium">Precio</th>
                    <th className="text-left px-4 py-2 text-sm font-medium">
                      Stock
                    </th>
                    <th className="text-left px-4 py-2 text-sm font-medium">
                      Min Stock
                    </th>
                    <th className="text-left px-4 py-2 text-sm font-medium">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {variants.map((variant) => (
                    <tr key={variant.id} className="border-b">
                      <td className="px-4 py-2">{variant.name}</td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          value={variant.price}
                          onChange={(e) =>
                            handleUpdateVariant(
                              variant.id,
                              'price',
                              parseFloat(e.target.value)
                            )
                          }
                          className="w-20 border rounded px-2 py-1"
                          step="0.01"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          value={variant.stock_quantity}
                          onChange={(e) =>
                            handleUpdateVariant(
                              variant.id,
                              'stock_quantity',
                              parseFloat(e.target.value)
                            )
                          }
                          className="w-20 border rounded px-2 py-1"
                          step="0.1"
                          disabled={formData.has_recipe}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          value={variant.min_stock}
                          onChange={(e) =>
                            handleUpdateVariant(
                              variant.id,
                              'min_stock',
                              parseFloat(e.target.value)
                            )
                          }
                          className="w-20 border rounded px-2 py-1"
                          step="0.1"
                          disabled={formData.has_recipe}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <button
                          onClick={() => handleDeleteVariant(variant.id)}
                          className="text-red-600 hover:bg-red-50 p-1 rounded"
                        >
                          <Trash2 size={18} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="border-t pt-4">
                <h3 className="font-medium mb-3">Agregar Variante</h3>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    placeholder="Nombre (Chico, Mediano...)"
                    value={newVariantForm.name}
                    onChange={(e) =>
                      setNewVariantForm({ ...newVariantForm, name: e.target.value })
                    }
                    className="border rounded px-3 py-2 text-sm"
                  />
                  <input
                    type="number"
                    placeholder="Precio"
                    value={newVariantForm.price}
                    onChange={(e) =>
                      setNewVariantForm({ ...newVariantForm, price: e.target.value })
                    }
                    className="border rounded px-3 py-2 text-sm"
                    step="0.01"
                  />
                  <input
                    type="number"
                    placeholder="Stock"
                    value={newVariantForm.stock_quantity}
                    onChange={(e) =>
                      setNewVariantForm({
                        ...newVariantForm,
                        stock_quantity: e.target.value,
                      })
                    }
                    className="border rounded px-3 py-2 text-sm"
                    disabled={formData.has_recipe}
                  />
                  <input
                    type="number"
                    placeholder="Min Stock"
                    value={newVariantForm.min_stock}
                    onChange={(e) =>
                      setNewVariantForm({
                        ...newVariantForm,
                        min_stock: e.target.value,
                      })
                    }
                    className="border rounded px-3 py-2 text-sm"
                    disabled={formData.has_recipe}
                  />
                </div>
                <button
                  onClick={handleAddVariant}
                  className="mt-3 flex items-center gap-2 bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700"
                >
                  <Plus size={16} /> Agregar
                </button>
              </div>
            </div>
          )}

          {activeTab === 'receta' && product?.has_recipe && product && (
            <div>
              {recipe.length > 0 && (
                <table className="w-full mb-6 border-collapse">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="text-left px-4 py-2 text-sm font-medium">
                        Insumo
                      </th>
                      <th className="text-left px-4 py-2 text-sm font-medium">
                        Cantidad
                      </th>
                      <th className="text-left px-4 py-2 text-sm font-medium">
                        Unidad
                      </th>
                      <th className="text-left px-4 py-2 text-sm font-medium">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {recipe.map((item, index) => (
                      <tr key={index} className="border-b">
                        <td className="px-4 py-2">{item.supply_name}</td>
                        <td className="px-4 py-2">{item.quantity}</td>
                        <td className="px-4 py-2">{item.unit}</td>
                        <td className="px-4 py-2">
                          <button
                            onClick={() => handleDeleteRecipeItem(index)}
                            className="text-red-600 hover:bg-red-50 p-1 rounded"
                          >
                            <Trash2 size={18} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              <div className="border-t pt-4">
                <h3 className="font-medium mb-3">Agregar Insumo a Receta</h3>
                <p className="text-sm text-gray-600 mb-3">
                  (Las cantidades se deducirán del stock de insumos al vender)
                </p>
                <div className="grid grid-cols-3 gap-3">
                  <select
                    value={newRecipeForm.supply_id}
                    onChange={(e) =>
                      setNewRecipeForm({
                        ...newRecipeForm,
                        supply_id: e.target.value,
                      })
                    }
                    className="border rounded px-3 py-2 text-sm"
                  >
                    <option value="">Seleccionar insumo</option>
                  </select>
                  <input
                    type="number"
                    placeholder="Cantidad"
                    value={newRecipeForm.quantity}
                    onChange={(e) =>
                      setNewRecipeForm({
                        ...newRecipeForm,
                        quantity: e.target.value,
                      })
                    }
                    className="border rounded px-3 py-2 text-sm"
                    step="0.01"
                  />
                  <input
                    type="text"
                    placeholder="Unidad (kg, litro...)"
                    value={newRecipeForm.unit}
                    onChange={(e) =>
                      setNewRecipeForm({ ...newRecipeForm, unit: e.target.value })
                    }
                    className="border rounded px-3 py-2 text-sm"
                  />
                </div>
                <button
                  onClick={handleAddRecipeItem}
                  className="mt-3 flex items-center gap-2 bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700"
                >
                  <Plus size={16} /> Agregar a Receta
                </button>
              </div>
            </div>
          )}

          {activeTab === 'receta' && !product?.has_recipe && (
            <div className="text-gray-500 text-center py-8">
              Este producto no tiene receta. Activa la opción "Tiene receta" en la
              pestaña Información para poder definir insumos.
            </div>
          )}

          {activeTab === 'historial' && (
            <div className="text-gray-500 text-center py-8">
              El historial de ventas se mostrará aquí (próximamente)
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ProductDetail
```

- [ ] **Step 2: Actualizar import en `frontend/src/App.jsx`**

Cambiar la línea:
```javascript
import ProductDetail from './pages/ProductDetail'
```

(Ya debería estar así después de Task 7)

- [ ] **Step 3: Probar en el navegador**

```bash
cd frontend
npm run dev
```

Ir a http://localhost:5173/products/new

Verificar:
- Página carga correctamente
- Tabs cambian al hacer click
- Info tab: se pueden llenar campos
- Botón Guardar funciona (crea nuevo producto)
- Variantes tab: se pueden agregar variantes
- Receta tab: aparece si has_recipe está activado
- Volver a /products/id después de crear

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/ProductDetail.jsx
git commit -m "feat: add ProductDetail page with 4 tabs (info/variants/recipe/history)"
```

---

## Task 11: MesaCard + SalonFloorPlan components

**Files:**
- Create: `frontend/src/components/pos/MesaCard.jsx`
- Create: `frontend/src/components/pos/SalonFloorPlan.jsx`

- [ ] **Step 1: Crear `frontend/src/components/pos/MesaCard.jsx`**

```javascript
import { ChairIcon } from 'lucide-react'

const MesaCard = ({ mesa, onClick, isDragging, style }) => {
  const getStatusColor = () => {
    switch (mesa.status) {
      case 'libre':
        return 'bg-green-100 border-green-500'
      case 'ocupada':
        return 'bg-red-100 border-red-500'
      case 'reservada':
        return 'bg-yellow-100 border-yellow-500'
      default:
        return 'bg-gray-100 border-gray-400'
    }
  }

  const getStatusTextColor = () => {
    switch (mesa.status) {
      case 'libre':
        return 'text-green-700'
      case 'ocupada':
        return 'text-red-700'
      case 'reservada':
        return 'text-yellow-700'
      default:
        return 'text-gray-700'
    }
  }

  const getStatusIcon = () => {
    switch (mesa.status) {
      case 'ocupada':
        return '🪑'
      case 'reservada':
        return '📋'
      default:
        return '🪑'
    }
  }

  return (
    <div
      onClick={onClick}
      style={style}
      className={`
        border-2 rounded-lg p-3 text-center cursor-pointer transition-all
        ${getStatusColor()}
        ${isDragging ? 'shadow-lg scale-110' : 'hover:shadow-md'}
      `}
    >
      <div className="text-2xl mb-1">{getStatusIcon()}</div>
      <div className={`font-bold text-sm mb-1 ${getStatusTextColor()}`}>
        Mesa {mesa.number}
        {mesa.name && <span className="text-xs block">{mesa.name}</span>}
      </div>
      {mesa.status === 'ocupada' && mesa.total !== undefined && (
        <div className={`text-sm font-semibold ${getStatusTextColor()}`}>
          ${mesa.total}
        </div>
      )}
      {mesa.status === 'reservada' && mesa.time && (
        <div className="text-xs text-yellow-600">{mesa.time}</div>
      )}
      {mesa.capacity && (
        <div className="text-xs text-gray-600 mt-1">Cap: {mesa.capacity}</div>
      )}
      <div className={`text-xs font-medium mt-1 ${getStatusTextColor()}`}>
        {mesa.status === 'libre' && 'Libre'}
        {mesa.status === 'ocupada' && 'Ocupada'}
        {mesa.status === 'reservada' && 'Reservada'}
      </div>
    </div>
  )
}

export default MesaCard
```

- [ ] **Step 2: Crear `frontend/src/components/pos/SalonFloorPlan.jsx`**

```javascript
import MesaCard from './MesaCard'

const SalonFloorPlan = ({ mesas = [], onMesaClick, isEditMode, onMesaDrag, style }) => {
  const handleDragStart = (e, mesa) => {
    if (!isEditMode) return
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('mesaId', mesa.id)
  }

  const handleDragOver = (e) => {
    if (!isEditMode) return
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = (e, x, y) => {
    if (!isEditMode) return
    e.preventDefault()
    const mesaId = parseInt(e.dataTransfer.getData('mesaId'))
    if (onMesaDrag) {
      onMesaDrag(mesaId, x, y)
    }
  }

  return (
    <div
      className={`
        relative w-full bg-slate-100 border-2 border-slate-300 rounded-lg
        ${isEditMode ? 'cursor-move' : 'cursor-default'}
      `}
      style={{
        height: '400px',
        minHeight: '400px',
        ...style,
      }}
      onDragOver={handleDragOver}
      onDrop={(e) => {
        const rect = e.currentTarget.getBoundingClientRect()
        const x = ((e.clientX - rect.left) / rect.width) * 100
        const y = ((e.clientY - rect.top) / rect.height) * 100
        handleDrop(e, x, y)
      }}
    >
      {mesas.map((mesa) => (
        <div
          key={mesa.id}
          onClick={() => !isEditMode && onMesaClick?.(mesa)}
          draggable={isEditMode}
          onDragStart={(e) => handleDragStart(e, mesa)}
          style={{
            position: 'absolute',
            left: `${mesa.pos_x}%`,
            top: `${mesa.pos_y}%`,
            width: `${mesa.width}%`,
            height: `${mesa.height}%`,
            minWidth: '60px',
            minHeight: '60px',
          }}
          className={isEditMode ? 'opacity-70' : ''}
        >
          <MesaCard mesa={mesa} />
        </div>
      ))}

      {isEditMode && (
        <div className="absolute bottom-2 right-2 bg-blue-500 text-white text-xs px-2 py-1 rounded">
          Modo edición activado
        </div>
      )}
    </div>
  )
}

export default SalonFloorPlan
```

- [ ] **Step 3: Verificar que los imports funcionan**

```bash
cd frontend
npm run dev
```

Abrir la consola del navegador. No debe haber errores de imports.

- [ ] **Step 4: Crear directorio si no existe**

```bash
mkdir -p frontend/src/components/pos
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/pos/MesaCard.jsx \
        frontend/src/components/pos/SalonFloorPlan.jsx
git commit -m "feat: add MesaCard and SalonFloorPlan POS components"
```

---

## Task 12: PosModal (grilla productos + comanda)

**Files:**
- Create: `frontend/src/components/pos/PosModal.jsx`

- [ ] **Step 1: Crear `frontend/src/components/pos/PosModal.jsx`**

```javascript
import { useState, useEffect } from 'react'
import { X, Plus, Minus } from 'lucide-react'
import productsService from '../../services/productsService'
import productCategoriesService from '../../services/productCategoriesService'

const PosModal = ({ mesaId, onClose, onSale }) => {
  const [categories, setCategories] = useState([])
  const [products, setProducts] = useState([])
  const [activeCategory, setActiveCategory] = useState(null)
  const [selectedVariant, setSelectedVariant] = useState(null)
  const [order, setOrder] = useState([])
  const [medioPago, setMedioPago] = useState('Efectivo')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [catsRes, prodsRes] = await Promise.all([
        productCategoriesService.getCategories({ include_inactive: false }),
        productsService.getProducts({ per_page: 100, include_inactive: false }),
      ])

      setCategories(catsRes.categories || [])
      setProducts(prodsRes.products || [])

      if (catsRes.categories && catsRes.categories.length > 0) {
        setActiveCategory(catsRes.categories[0].id)
      }
    } catch (err) {
      setError('Error al cargar productos')
    } finally {
      setLoading(false)
    }
  }

  const filteredProducts = activeCategory
    ? products.filter((p) => p.category_id === activeCategory && p.is_active)
    : products.filter((p) => p.is_active)

  const handleAddProduct = (product) => {
    if (product.variants && product.variants.length > 1) {
      setSelectedVariant({ product, selectingVariant: true })
      return
    }

    const variant = product.variants?.[0]
    if (!variant) {
      setError('No hay variantes disponibles')
      return
    }

    addToOrder(variant, product)
  }

  const addToOrder = (variant, product) => {
    const existingItem = order.find(
      (item) => item.product_variant_id === variant.id
    )

    if (existingItem) {
      setOrder(
        order.map((item) =>
          item.product_variant_id === variant.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        )
      )
    } else {
      setOrder([
        ...order,
        {
          product_variant_id: variant.id,
          product_name: product.name,
          variant_name: variant.name,
          quantity: 1,
          unit_price: variant.price,
          subtotal: variant.price,
        },
      ])
    }
    setSelectedVariant(null)
    setError('')
  }

  const handleQuantityChange = (variantId, delta) => {
    setOrder(
      order
        .map((item) => {
          if (item.product_variant_id === variantId) {
            const newQty = Math.max(1, item.quantity + delta)
            return {
              ...item,
              quantity: newQty,
              subtotal: item.unit_price * newQty,
            }
          }
          return item
        })
        .filter((item) => item.quantity > 0)
    )
  }

  const handleRemoveItem = (variantId) => {
    setOrder(order.filter((item) => item.product_variant_id !== variantId))
  }

  const totalAmount = order.reduce((sum, item) => sum + item.subtotal, 0)

  const handleCobrar = async () => {
    if (order.length === 0) {
      setError('Agrega al menos un item')
      return
    }

    setSaving(true)
    try {
      await onSale({
        items: order.map((item) => ({
          product_variant_id: item.product_variant_id,
          quantity: item.quantity,
        })),
        mesa_id: mesaId,
        medio_pago: medioPago,
      })
      onClose()
    } catch (err) {
      setError(err.response?.data?.error || 'Error al guardar venta')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">Cargando...</div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold">
            {mesaId ? `Mesa ${mesaId}` : 'Nueva Venta'} - POS
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded"
            disabled={saving}
          >
            <X size={24} />
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border-b border-red-200 text-red-700 px-6 py-3">
            {error}
          </div>
        )}

        <div className="flex-1 overflow-hidden flex gap-4 p-6">
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex gap-2 mb-4 pb-4 border-b overflow-x-auto">
              <button
                onClick={() => setActiveCategory(null)}
                className={`px-4 py-2 rounded whitespace-nowrap ${
                  activeCategory === null
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                Todos
              </button>
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  className={`px-4 py-2 rounded whitespace-nowrap ${
                    activeCategory === cat.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  {cat.icon} {cat.name}
                </button>
              ))}
            </div>

            <div className="overflow-y-auto flex-1">
              <div className="grid grid-cols-3 gap-3">
                {filteredProducts.map((product) => (
                  <button
                    key={product.id}
                    onClick={() => handleAddProduct(product)}
                    className="border-2 border-gray-300 rounded-lg p-3 hover:border-blue-500 hover:bg-blue-50 transition text-center"
                  >
                    <div className="text-3xl mb-2">📦</div>
                    <div className="font-medium text-sm">{product.name}</div>
                    {product.variants && product.variants.length > 0 && (
                      <div className="text-xs text-gray-600 mt-1">
                        ${product.variants[0].price}
                        {product.variants.length > 1 && ` +${product.variants.length - 1}`}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="w-64 border-l pl-4 flex flex-col">
            <h3 className="font-bold text-lg mb-3">Comanda</h3>

            <div className="flex-1 overflow-y-auto mb-4 border rounded p-3 bg-gray-50">
              {order.length === 0 ? (
                <div className="text-center text-gray-500 py-4">Sin items</div>
              ) : (
                <div className="space-y-2">
                  {order.map((item) => (
                    <div key={item.product_variant_id} className="bg-white p-2 rounded">
                      <div className="text-sm font-medium">{item.product_name}</div>
                      <div className="text-xs text-gray-600">{item.variant_name}</div>
                      <div className="flex items-center justify-between mt-1">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() =>
                              handleQuantityChange(item.product_variant_id, -1)
                            }
                            className="p-0.5 hover:bg-red-100 rounded"
                          >
                            <Minus size={14} />
                          </button>
                          <span className="w-6 text-center text-sm">
                            {item.quantity}
                          </span>
                          <button
                            onClick={() =>
                              handleQuantityChange(item.product_variant_id, 1)
                            }
                            className="p-0.5 hover:bg-green-100 rounded"
                          >
                            <Plus size={14} />
                          </button>
                        </div>
                        <div className="text-sm font-medium">
                          ${item.subtotal.toFixed(2)}
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveItem(item.product_variant_id)}
                        className="text-xs text-red-600 hover:underline mt-1"
                      >
                        Eliminar
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="border-t pt-3 mb-3">
              <div className="flex justify-between items-center font-bold text-lg mb-3">
                <span>Total:</span>
                <span className="text-green-600">${totalAmount.toFixed(2)}</span>
              </div>

              <div className="mb-3">
                <label className="block text-sm font-medium mb-2">
                  Medio de Pago
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {['Efectivo', 'Débito', 'QR'].map((option) => (
                    <button
                      key={option}
                      onClick={() => setMedioPago(option)}
                      className={`py-2 rounded text-sm font-medium transition ${
                        medioPago === option
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={handleCobrar}
                disabled={saving || order.length === 0}
                className="w-full bg-green-600 text-white font-bold py-3 rounded hover:bg-green-700 disabled:bg-gray-400 transition"
              >
                {saving ? 'Guardando...' : 'COBRAR'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {selectedVariant && selectedVariant.selectingVariant && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-51">
          <div className="bg-white rounded-lg p-6 max-w-sm">
            <h3 className="text-lg font-bold mb-4">
              Selecciona tamaño: {selectedVariant.product.name}
            </h3>
            <div className="space-y-2 mb-4">
              {selectedVariant.product.variants.map((variant) => (
                <button
                  key={variant.id}
                  onClick={() =>
                    addToOrder(variant, selectedVariant.product)
                  }
                  className="w-full border-2 border-blue-500 bg-blue-50 text-blue-700 font-medium py-2 rounded hover:bg-blue-100 transition"
                >
                  {variant.name} - ${variant.price}
                </button>
              ))}
            </div>
            <button
              onClick={() => setSelectedVariant(null)}
              className="w-full border-2 border-gray-300 py-2 rounded hover:bg-gray-50"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default PosModal
```

- [ ] **Step 2: Probar que el código está sintácticamente correcto**

```bash
cd frontend
npm run dev
```

Abrir consola del navegador. No debe haber errores de imports/sintaxis en PosModal.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/pos/PosModal.jsx
git commit -m "feat: add PosModal with product grid and order sidebar"
```

---

## Task 13: OrderDrawer + página /pos

**Files:**
- Create: `frontend/src/components/pos/OrderDrawer.jsx`
- Create: `frontend/src/pages/Pos.jsx`

- [ ] **Step 1: Crear `frontend/src/components/pos/OrderDrawer.jsx`**

```javascript
import { X, Plus } from 'lucide-react'

const OrderDrawer = ({ mesa, saleData, onAddItem, onClose, onCobrar }) => {
  const total = saleData?.items?.reduce((sum, item) => sum + item.subtotal, 0) || 0
  const duration = saleData?.duration || '0 min'

  return (
    <div className="fixed right-0 top-0 bottom-0 w-96 bg-white shadow-xl z-40 flex flex-col">
      <div className="border-b p-4 flex justify-between items-center">
        <h3 className="text-lg font-bold">Mesa {mesa.number}</h3>
        <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
          <X size={20} />
        </button>
      </div>

      <div className="text-xs text-gray-600 px-4 pt-3">
        Abierta hace {duration}
      </div>

      <div className="flex-1 overflow-y-auto p-4 border-b">
        {!saleData?.items || saleData.items.length === 0 ? (
          <div className="text-center text-gray-500 py-8">Sin items</div>
        ) : (
          <div className="space-y-2">
            {saleData.items.map((item, idx) => (
              <div
                key={idx}
                className="bg-gray-50 rounded p-2 border border-gray-200"
              >
                <div className="flex justify-between">
                  <div>
                    <div className="text-sm font-medium">{item.product_name}</div>
                    <div className="text-xs text-gray-600">
                      {item.variant_name}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">
                      ${item.subtotal.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-600">x{item.quantity}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="p-4 border-b">
        <div className="flex justify-between items-center font-bold text-lg mb-3">
          <span>Total:</span>
          <span className="text-green-600">${total.toFixed(2)}</span>
        </div>
        <button
          onClick={onAddItem}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 text-sm font-medium mb-2"
        >
          <Plus size={16} className="inline mr-1" /> Agregar Ítem
        </button>
      </div>

      <div className="p-4 space-y-2">
        <button
          onClick={onCobrar}
          className="w-full bg-green-600 text-white font-bold py-3 rounded hover:bg-green-700 text-lg"
        >
          COBRAR
        </button>
        <button
          onClick={onClose}
          className="w-full border-2 border-gray-300 py-2 rounded hover:bg-gray-50 text-sm font-medium"
        >
          Cerrar Drawer
        </button>
      </div>
    </div>
  )
}

export default OrderDrawer
```

- [ ] **Step 2: Crear `frontend/src/pages/Pos.jsx`**

```javascript
import { useState, useEffect } from 'react'
import { Settings2 } from 'lucide-react'
import salonsService from '../services/salonsService'
import salesService from '../services/salesService'
import PosModal from '../components/pos/PosModal'
import OrderDrawer from '../components/pos/OrderDrawer'
import SalonFloorPlan from '../components/pos/SalonFloorPlan'

const Pos = () => {
  const [salons, setSalons] = useState([])
  const [activeSalon, setActiveSalon] = useState(null)
  const [mesas, setMesas] = useState([])
  const [dailySummary, setDailySummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editMode, setEditMode] = useState(false)

  const [showPosModal, setShowPosModal] = useState(false)
  const [selectedMesa, setSelectedMesa] = useState(null)
  const [showOrderDrawer, setShowOrderDrawer] = useState(false)
  const [orderData, setOrderData] = useState(null)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchDailySummary, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (activeSalon) {
      fetchMesas(activeSalon)
    }
  }, [activeSalon])

  const fetchData = async () => {
    try {
      const salonRes = await salonsService.getSalons({
        include_inactive: false,
      })
      setSalons(salonRes.salons || [])

      if (salonRes.salons && salonRes.salons.length > 0) {
        setActiveSalon(salonRes.salons[0].id)
      }

      await fetchDailySummary()
    } catch (err) {
      setError('Error al cargar salones')
    } finally {
      setLoading(false)
    }
  }

  const fetchMesas = async (salonId) => {
    try {
      const response = await salonsService.getMesas(salonId)
      setMesas(response.mesas || [])
    } catch (err) {
      setError('Error al cargar mesas')
    }
  }

  const fetchDailySummary = async () => {
    try {
      const response = await salesService.getDailySummary()
      setDailySummary(response)
    } catch (err) {
      console.error('Error fetching daily summary:', err)
    }
  }

  const handleMesaClick = (mesa) => {
    if (mesa.status === 'libre') {
      setSelectedMesa(mesa)
      setShowPosModal(true)
    } else if (mesa.status === 'ocupada') {
      setSelectedMesa(mesa)
      setOrderData({
        items: [
          {
            product_name: 'Sample',
            variant_name: 'Test',
            quantity: 1,
            subtotal: 100,
          },
        ],
      })
      setShowOrderDrawer(true)
    }
  }

  const handleSale = async (saleData) => {
    try {
      await salesService.createSale(
        saleData.items,
        saleData.mesa_id,
        saleData.medio_pago
      )

      await fetchMesas(activeSalon)
      await fetchDailySummary()

      setShowPosModal(false)
      setSelectedMesa(null)
      setError('')
    } catch (err) {
      setError(err.response?.data?.error || 'Error al registrar venta')
    }
  }

  const handleAddItem = () => {
    setShowOrderDrawer(false)
    setShowPosModal(true)
  }

  if (loading) {
    return <div className="p-6">Cargando POS...</div>
  }

  const currentSalon = salons.find((s) => s.id === activeSalon)

  return (
    <div className="h-screen flex flex-col bg-slate-900 text-white">
      <div className="p-4 border-b border-slate-700">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold">🛒 Caja — {currentSalon?.name}</h1>
          <div className="flex gap-2 text-xs">
            <span className="text-green-400">● {mesas.filter((m) => m.status === 'libre').length} libres</span>
            <span className="text-red-400">● {mesas.filter((m) => m.status === 'ocupada').length} ocupadas</span>
            {mesas.filter((m) => m.status === 'reservada').length > 0 && (
              <span className="text-yellow-400">
                ● {mesas.filter((m) => m.status === 'reservada').length} reservadas
              </span>
            )}
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto">
          {salons.map((salon) => (
            <button
              key={salon.id}
              onClick={() => setActiveSalon(salon.id)}
              className={`px-4 py-2 rounded whitespace-nowrap transition ${
                activeSalon === salon.id
                  ? 'bg-green-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {salon.name}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="bg-red-900 border-b border-red-700 text-red-200 px-4 py-2">
          {error}
        </div>
      )}

      <div className="flex-1 relative overflow-hidden p-4">
        {activeSalon && (
          <SalonFloorPlan
            mesas={mesas}
            onMesaClick={handleMesaClick}
            isEditMode={editMode}
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
            }}
          />
        )}

        <button
          onClick={() => setEditMode(!editMode)}
          className={`absolute bottom-6 right-6 flex items-center gap-2 px-4 py-2 rounded transition ${
            editMode
              ? 'bg-yellow-600 hover:bg-yellow-700'
              : 'bg-slate-700 hover:bg-slate-600'
          }`}
        >
          <Settings2 size={18} /> {editMode ? 'Guardar Plano' : '⚙️ Editar Plano'}
        </button>
      </div>

      <div className="border-t border-slate-700 p-4 bg-slate-800">
        <div className="flex gap-6 text-sm justify-center">
          {dailySummary && (
            <>
              <div>
                <span className="text-green-400 font-bold">
                  ${dailySummary.total_vendido.toFixed(2)}
                </span>
                <span className="text-slate-400 ml-2">vendidos hoy</span>
              </div>
              <div>
                <span className="text-purple-400 font-bold">
                  {dailySummary.cantidad_ventas}
                </span>
                <span className="text-slate-400 ml-2">ventas</span>
              </div>
              {dailySummary.bajo_stock_count > 0 && (
                <div className="text-red-400">
                  ⚠️ {dailySummary.bajo_stock_count} con stock bajo
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {showPosModal && (
        <PosModal
          mesaId={selectedMesa?.id}
          onClose={() => {
            setShowPosModal(false)
            setSelectedMesa(null)
          }}
          onSale={handleSale}
        />
      )}

      {showOrderDrawer && selectedMesa && (
        <OrderDrawer
          mesa={selectedMesa}
          saleData={orderData}
          onAddItem={handleAddItem}
          onClose={() => {
            setShowOrderDrawer(false)
            setSelectedMesa(null)
            setOrderData(null)
          }}
          onCobrar={() => {
            setShowOrderDrawer(false)
            setSelectedMesa(null)
          }}
        />
      )}
    </div>
  )
}

export default Pos
```

- [ ] **Step 3: Actualizar import en `frontend/src/App.jsx`**

Cambiar la línea (ya debería estar):
```javascript
import Pos from './pages/Pos'
```

- [ ] **Step 4: Probar en el navegador**

```bash
cd frontend
npm run dev
```

Ir a http://localhost:5173/pos

Verificar:
- Página carga
- Salones aparecen en tabs
- Mesas se muestran en el plano con posiciones
- Click en mesa libre abre PosModal
- Click en mesa ocupada abre OrderDrawer
- Resumen del día aparece en la barra inferior
- Botón "Editar Plano" aparece

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/pos/OrderDrawer.jsx \
        frontend/src/pages/Pos.jsx
git commit -m "feat: add Pos page with salon tabs and order management"
```

---

## Task 14: FloorPlanEditor (drag-and-drop mode)

**Files:**
- Create: `frontend/src/components/pos/FloorPlanEditor.jsx`

- [ ] **Step 1: Crear `frontend/src/components/pos/FloorPlanEditor.jsx`**

```javascript
import { useState } from 'react'
import { Save, X, Plus, Trash2 } from 'lucide-react'
import salonsService from '../../services/salonsService'

const FloorPlanEditor = ({ salon, mesas, onSave, onClose }) => {
  const [editingMesas, setEditingMesas] = useState(mesas)
  const [draggingMesa, setDraggingMesa] = useState(null)
  const [resizingMesa, setResizingMesa] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [newMesaForm, setNewMesaForm] = useState({
    number: '',
    name: '',
    capacity: '',
    pos_x: 50,
    pos_y: 50,
    width: 8,
    height: 8,
  })
  const [showNewMesaForm, setShowNewMesaForm] = useState(false)

  const handleMesaDragStart = (e, mesa) => {
    setDraggingMesa(mesa)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handlePlanDragOver = (e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handlePlanDrop = (e) => {
    e.preventDefault()
    if (!draggingMesa) return

    const rect = e.currentTarget.getBoundingClientRect()
    const x = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100))
    const y = Math.max(0, Math.min(100, ((e.clientY - rect.top) / rect.height) * 100))

    setEditingMesas(
      editingMesas.map((m) =>
        m.id === draggingMesa.id ? { ...m, pos_x: x, pos_y: y } : m
      )
    )
    setDraggingMesa(null)
  }

  const handleResizeStart = (e, mesa) => {
    e.preventDefault()
    setResizingMesa({
      ...mesa,
      startX: e.clientX,
      startY: e.clientY,
      startWidth: mesa.width,
      startHeight: mesa.height,
    })
  }

  const handleMouseMove = (e) => {
    if (!resizingMesa) return

    const deltaX = e.clientX - resizingMesa.startX
    const deltaY = e.clientY - resizingMesa.startY

    const newWidth = Math.max(5, resizingMesa.startWidth + deltaX / 10)
    const newHeight = Math.max(5, resizingMesa.startHeight + deltaY / 10)

    setEditingMesas(
      editingMesas.map((m) =>
        m.id === resizingMesa.id
          ? { ...m, width: newWidth, height: newHeight }
          : m
      )
    )
  }

  const handleMouseUp = () => {
    setResizingMesa(null)
  }

  const handleDeleteMesa = (mesaId) => {
    if (window.confirm('¿Desactivar esta mesa?')) {
      setEditingMesas(editingMesas.filter((m) => m.id !== mesaId))
    }
  }

  const handleAddNewMesa = async () => {
    if (!newMesaForm.number) {
      setError('El número de mesa es requerido')
      return
    }

    try {
      const newMesa = await salonsService.createMesa(salon.id, {
        number: parseInt(newMesaForm.number),
        name: newMesaForm.name || null,
        capacity: newMesaForm.capacity ? parseInt(newMesaForm.capacity) : null,
        pos_x: newMesaForm.pos_x,
        pos_y: newMesaForm.pos_y,
        width: newMesaForm.width,
        height: newMesaForm.height,
        status: 'libre',
      })

      setEditingMesas([...editingMesas, newMesa])
      setNewMesaForm({
        number: '',
        name: '',
        capacity: '',
        pos_x: 50,
        pos_y: 50,
        width: 8,
        height: 8,
      })
      setShowNewMesaForm(false)
      setError('')
    } catch (err) {
      setError(err.response?.data?.error || 'Error al crear mesa')
    }
  }

  const handleSaveLayout = async () => {
    setSaving(true)
    try {
      for (const mesa of editingMesas) {
        if (mesa.id) {
          await salonsService.updateMesa(salon.id, mesa.id, {
            pos_x: mesa.pos_x,
            pos_y: mesa.pos_y,
            width: mesa.width,
            height: mesa.height,
          })
        }
      }

      setError('')
      onSave()
    } catch (err) {
      setError('Error al guardar plano')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold">Editar Plano - {salon.name}</h2>
          <button
            onClick={onClose}
            disabled={saving}
            className="p-2 hover:bg-gray-100 rounded"
          >
            <X size={24} />
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border-b border-red-200 text-red-700 px-6 py-3">
            {error}
          </div>
        )}

        <div className="flex-1 overflow-hidden flex gap-4 p-6">
          <div className="flex-1 flex flex-col">
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                Arrastra las mesas para reposicionarlas. Haz click y arrastra desde la esquina inferior derecha para redimensionar.
              </p>
            </div>

            <div
              className="flex-1 bg-slate-100 border-2 border-slate-300 rounded-lg relative overflow-hidden cursor-move"
              onDragOver={handlePlanDragOver}
              onDrop={handlePlanDrop}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
            >
              {editingMesas.map((mesa) => (
                <div
                  key={mesa.id}
                  draggable
                  onDragStart={(e) => handleMesaDragStart(e, mesa)}
                  style={{
                    position: 'absolute',
                    left: `${mesa.pos_x}%`,
                    top: `${mesa.pos_y}%`,
                    width: `${mesa.width}%`,
                    height: `${mesa.height}%`,
                    minWidth: '60px',
                    minHeight: '60px',
                  }}
                  className="border-2 border-blue-500 bg-blue-100 rounded-lg p-2 cursor-move flex flex-col justify-between group"
                >
                  <div className="text-center">
                    <div className="font-bold text-sm">Mesa {mesa.number}</div>
                    {mesa.name && <div className="text-xs">{mesa.name}</div>}
                  </div>

                  <div
                    className="absolute bottom-0 right-0 w-4 h-4 bg-blue-500 cursor-se-resize opacity-0 group-hover:opacity-100 rounded-tl"
                    onMouseDown={(e) => handleResizeStart(e, mesa)}
                  />

                  <button
                    onClick={() => handleDeleteMesa(mesa.id)}
                    className="absolute -top-3 -right-3 bg-red-500 text-white p-1 rounded-full hover:bg-red-600 opacity-0 group-hover:opacity-100 transition"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="w-80 border-l pl-4 flex flex-col">
            <h3 className="font-bold text-lg mb-4">Mesas ({editingMesas.length})</h3>

            <div className="flex-1 overflow-y-auto mb-4 space-y-2 text-sm">
              {editingMesas.map((mesa) => (
                <div key={mesa.id} className="bg-gray-50 p-2 rounded border">
                  <div className="font-medium">Mesa {mesa.number}</div>
                  <div className="text-xs text-gray-600">
                    Pos: ({mesa.pos_x.toFixed(1)}, {mesa.pos_y.toFixed(1)})
                  </div>
                  <div className="text-xs text-gray-600">
                    Tamaño: {mesa.width.toFixed(1)} x {mesa.height.toFixed(1)}
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t pt-4">
              <h4 className="font-medium mb-3">Agregar Mesa</h4>

              {!showNewMesaForm ? (
                <button
                  onClick={() => setShowNewMesaForm(true)}
                  className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 flex items-center justify-center gap-2 text-sm font-medium"
                >
                  <Plus size={16} /> Nueva Mesa
                </button>
              ) : (
                <div className="space-y-2 text-sm">
                  <input
                    type="number"
                    placeholder="Número"
                    value={newMesaForm.number}
                    onChange={(e) =>
                      setNewMesaForm({
                        ...newMesaForm,
                        number: e.target.value,
                      })
                    }
                    className="w-full border rounded px-2 py-1"
                  />
                  <input
                    type="text"
                    placeholder="Nombre (opcional)"
                    value={newMesaForm.name}
                    onChange={(e) =>
                      setNewMesaForm({ ...newMesaForm, name: e.target.value })
                    }
                    className="w-full border rounded px-2 py-1"
                  />
                  <input
                    type="number"
                    placeholder="Capacidad (opcional)"
                    value={newMesaForm.capacity}
                    onChange={(e) =>
                      setNewMesaForm({
                        ...newMesaForm,
                        capacity: e.target.value,
                      })
                    }
                    className="w-full border rounded px-2 py-1"
                  />

                  <div className="grid grid-cols-2 gap-1">
                    <input
                      type="number"
                      placeholder="Pos X"
                      value={newMesaForm.pos_x}
                      onChange={(e) =>
                        setNewMesaForm({
                          ...newMesaForm,
                          pos_x: parseFloat(e.target.value),
                        })
                      }
                      className="border rounded px-2 py-1 text-xs"
                      step="1"
                    />
                    <input
                      type="number"
                      placeholder="Pos Y"
                      value={newMesaForm.pos_y}
                      onChange={(e) =>
                        setNewMesaForm({
                          ...newMesaForm,
                          pos_y: parseFloat(e.target.value),
                        })
                      }
                      className="border rounded px-2 py-1 text-xs"
                      step="1"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-1">
                    <input
                      type="number"
                      placeholder="Ancho"
                      value={newMesaForm.width}
                      onChange={(e) =>
                        setNewMesaForm({
                          ...newMesaForm,
                          width: parseFloat(e.target.value),
                        })
                      }
                      className="border rounded px-2 py-1 text-xs"
                      step="1"
                    />
                    <input
                      type="number"
                      placeholder="Alto"
                      value={newMesaForm.height}
                      onChange={(e) =>
                        setNewMesaForm({
                          ...newMesaForm,
                          height: parseFloat(e.target.value),
                        })
                      }
                      className="border rounded px-2 py-1 text-xs"
                      step="1"
                    />
                  </div>

                  <div className="flex gap-1">
                    <button
                      onClick={handleAddNewMesa}
                      className="flex-1 bg-green-600 text-white py-1 rounded text-xs font-medium hover:bg-green-700"
                    >
                      Agregar
                    </button>
                    <button
                      onClick={() => setShowNewMesaForm(false)}
                      className="flex-1 bg-gray-300 text-gray-700 py-1 rounded text-xs font-medium hover:bg-gray-400"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="border-t pt-4 flex gap-2">
              <button
                onClick={handleSaveLayout}
                disabled={saving}
                className="flex-1 bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-gray-400 flex items-center justify-center gap-2 font-medium"
              >
                <Save size={18} />
                {saving ? 'Guardando...' : 'Guardar'}
              </button>
              <button
                onClick={onClose}
                className="flex-1 border-2 border-gray-300 py-2 rounded hover:bg-gray-50"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FloorPlanEditor
```

- [ ] **Step 2: Integrar en página /pos**

En `frontend/src/pages/Pos.jsx`, agregar import:
```javascript
import FloorPlanEditor from '../components/pos/FloorPlanEditor'
```

Y modificar el botón "Editar Plano" para usar el editor. Cambiar donde dice:
```javascript
<button
  onClick={() => setEditMode(!editMode)}
  className={...}
>
```

Por:
```javascript
<button
  onClick={() => {
    if (editMode) {
      // Guarda y cierra
      setEditMode(false)
    } else {
      // Abre editor
      setShowFloorEditor(true)
    }
  }}
  className={...}
>
```

Y agregar estado:
```javascript
const [showFloorEditor, setShowFloorEditor] = useState(false)
```

Al final del componente, agregar:
```javascript
{showFloorEditor && activeSalon && (
  <FloorPlanEditor
    salon={currentSalon}
    mesas={mesas}
    onSave={() => {
      setShowFloorEditor(false)
      fetchMesas(activeSalon)
    }}
    onClose={() => setShowFloorEditor(false)}
  />
)}
```

- [ ] **Step 3: Probar en el navegador**

```bash
cd frontend
npm run dev
```

Ir a http://localhost:5173/pos

Verificar:
- Botón "Editar Plano" abre el modal editor
- Mesas se pueden arrastrar en el editor
- Mesas se pueden redimensionar desde la esquina
- Se puede agregar nueva mesa
- Se puede eliminar mesa
- Guardar persiste los cambios en la BD

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/pos/FloorPlanEditor.jsx
git commit -m "feat: add FloorPlanEditor with drag-and-drop mesas layout"
```

---

## Task 15: Página /stock (inventario unificado)

**Files:**
- Create: `frontend/src/pages/Stock.jsx`

- [ ] **Step 1: Crear `frontend/src/pages/Stock.jsx`**

```javascript
import { useState, useEffect } from 'react'
import { AlertCircle } from 'lucide-react'
import productsService from '../services/productsService'

const Stock = () => {
  const [variants, setVariants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updatingId, setUpdatingId] = useState(null)

  useEffect(() => {
    fetchLowStock()
  }, [])

  const fetchLowStock = async () => {
    setLoading(true)
    try {
      const response = await productsService.getLowStock()
      setVariants(response.variants || [])
      setError('')
    } catch (err) {
      setError('Error al cargar el inventario')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleStockChange = async (variantId, productId, newQuantity) => {
    setUpdatingId(variantId)
    try {
      await productsService.adjustStock(productId, variantId, newQuantity)
      setVariants(
        variants.map((v) =>
          v.id === variantId
            ? { ...v, stock_quantity: newQuantity }
            : v
        )
      )
      setError('')
    } catch (err) {
      setError('Error al actualizar stock')
    } finally {
      setUpdatingId(null)
    }
  }

  if (loading) {
    return <div className="p-6">Cargando inventario...</div>
  }

  const lowStockVariants = variants.filter(
    (v) => v.stock_quantity <= v.min_stock
  )
  const normalStockVariants = variants.filter(
    (v) => v.stock_quantity > v.min_stock
  )

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">📦 Inventario</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {lowStockVariants.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6 flex gap-3">
          <AlertCircle className="text-yellow-600 flex-shrink-0" size={20} />
          <div>
            <h3 className="font-bold text-yellow-900 mb-1">Alerta: Stock Bajo</h3>
            <p className="text-sm text-yellow-800">
              {lowStockVariants.length} productos tienen stock por debajo del mínimo
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Stock Directo */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b p-4 bg-blue-50">
            <h2 className="text-lg font-bold text-blue-900">
              Stock Directo (Variantes)
            </h2>
            <p className="text-sm text-blue-700 mt-1">
              {variants.length} items
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-sm text-gray-700">
                    Producto
                  </th>
                  <th className="text-right px-4 py-3 font-medium text-sm text-gray-700">
                    Stock
                  </th>
                  <th className="text-right px-4 py-3 font-medium text-sm text-gray-700">
                    Mín
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {variants.length === 0 ? (
                  <tr>
                    <td colSpan="3" className="px-4 py-4 text-center text-gray-500">
                      No hay variantes
                    </td>
                  </tr>
                ) : (
                  variants.map((variant) => {
                    const isLow = variant.stock_quantity <= variant.min_stock
                    return (
                      <tr
                        key={variant.id}
                        className={isLow ? 'bg-red-50 hover:bg-red-100' : 'hover:bg-gray-50'}
                      >
                        <td className="px-4 py-3">
                          <div className="font-medium text-sm">
                            {variant.product_name}
                          </div>
                          <div className="text-xs text-gray-600">
                            {variant.name}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <input
                            type="number"
                            value={variant.stock_quantity}
                            onChange={(e) =>
                              handleStockChange(
                                variant.id,
                                variant.product_id,
                                parseFloat(e.target.value)
                              )
                            }
                            disabled={updatingId === variant.id}
                            className={`w-20 border rounded px-2 py-1 text-right text-sm ${
                              isLow
                                ? 'border-red-300 bg-red-100 text-red-900'
                                : 'border-gray-300'
                            }`}
                            step="0.1"
                          />
                        </td>
                        <td className="px-4 py-3 text-right text-sm">
                          {variant.min_stock}
                          {isLow && (
                            <div className="text-red-600 font-bold text-xs mt-1">
                              ⚠️ BAJO
                            </div>
                          )}
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Insumos */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b p-4 bg-purple-50">
            <h2 className="text-lg font-bold text-purple-900">
              Insumos (Supplies)
            </h2>
            <p className="text-sm text-purple-700 mt-1">
              Stock disponible para recetas
            </p>
          </div>

          <div className="p-4 text-center text-gray-500">
            <p>Los insumos se gestionan en la sección de Productos</p>
            <p className="text-sm mt-2 text-gray-600">
              Al crear recetas, el stock de insumos se descuenta automáticamente
              al vender productos con receta.
            </p>
          </div>
        </div>
      </div>

      {/* Resumen */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-600">{variants.length}</div>
          <div className="text-sm text-blue-900">Variantes en Stock</div>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600">
            {normalStockVariants.length}
          </div>
          <div className="text-sm text-green-900">Stock Normal</div>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-red-600">
            {lowStockVariants.length}
          </div>
          <div className="text-sm text-red-900">Stock Bajo</div>
        </div>
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-bold text-blue-900 mb-2">ℹ️ Información</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>
            • <strong>Stock Directo:</strong> Para productos simples (sin receta)
          </li>
          <li>
            • <strong>Insumos:</strong> Ingredientes para productos con receta
          </li>
          <li>
            • <strong>Min Stock:</strong> Nivel mínimo. Se resalta en rojo si está
            por debajo
          </li>
          <li>
            • Edita los números directamente. Los cambios se guardan automáticamente
          </li>
        </ul>
      </div>
    </div>
  )
}

export default Stock
```

- [ ] **Step 2: Actualizar import en `frontend/src/App.jsx`**

Cambiar (ya debería estar):
```javascript
import Stock from './pages/Stock'
```

- [ ] **Step 3: Probar en el navegador**

```bash
cd frontend
npm run dev
```

Ir a http://localhost:5173/stock

Verificar:
- Página carga
- Muestra tabla de variantes/stock
- Se puede editar stock inline
- Resalta en rojo si está bajo mínimo
- Botón de actualización funciona
- Resumen de stats aparece

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Stock.jsx
git commit -m "feat: add Stock page with unified inventory management"
```

---

## Plan Completado ✅

Todas las 15 tareas están documentadas en el plan. Están organizadas en 4 capas:

**Capa 1: Datos (Tasks 1-6)** ✅
- Modelos SQLAlchemy (7 nuevos + 2 extensiones)
- Migración Alembic
- 3 blueprints (product_categories, products, salons)
- Extensiones a sales + stock_service
- Todos con tests

**Capa 2: Catálogo (Tasks 7-10)** ✅
- Servicios JS + Sidebar + App.jsx rutas
- Página ProductCategories (CRUD)
- Página Products (lista con filtros)
- Página ProductDetail (4 tabs: info/variantes/receta/historial)

**Capa 3: POS + Ventas (Tasks 11-14)** ✅
- MesaCard + SalonFloorPlan (componentes)
- PosModal (grilla productos + comanda)
- OrderDrawer + página /pos (nucleus del POS)
- FloorPlanEditor (drag-and-drop)

**Capa 4: Stock (Task 15)** ✅
- Página /stock (inventario unificado)

---

## Próximos Pasos

El plan está listo para implementación. Dos opciones:

**1. Subagent-Driven (Recomendado)**
- Invocar `superpowers:subagent-driven-development`
- Un subagent por task, revisión entre tasks, iteración rápida

**2. Inline Execution**
- Invocar `superpowers:executing-plans`
- Batch execution con checkpoints

¿Cuál prefieres? 🚀
