# POS: motor de venta (sub-proyecto 1a) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Backend del POS de Galia: modelo, reglas y API para ventas de salón y mostrador (tandas, modificadores, descuentos, cobros, mover, dividir, anular), con stock al confirmar, auditoría y proyección de las ventas cerradas en `sales`.

**Architecture:** Tablas `pos_*` propias. La lógica vive en `backend/app/services/pos/` (servicios que hacen una transacción completa cada uno, más `pricing.py` con funciones puras). Las rutas son delgadas: validan permisos con `module_required`, llaman al servicio y traducen `PosError` a JSON. Al cerrar, cada venta se copia como una fila en `sales` (`source='galia'`) para que los reportes actuales la vean.

**Tech Stack:** Flask, Flask-SQLAlchemy, Alembic (Flask-Migrate), pytest (SQLite en memoria; tests de concurrencia contra PostgreSQL opcional).

**Spec:** `docs/superpowers/specs/2026-10-09-pos-sales-engine-design.md`

---

## Convenciones

- **Worktree:** `C:\Users\onofr\Desktop\galia-app\.claude\worktrees\pos-base`, rama `feature/pos-sales`. Paths relativos a esa raíz.
- **Python:** `C:\Users\onofr\Desktop\galia-app\backend\venv\Scripts\python.exe` (en el plan: `PY`). Los tests se corren con cwd = `backend/`. Si Bash rechaza el comando, usar PowerShell: `Set-Location C:\Users\onofr\Desktop\galia-app\.claude\worktrees\pos-base\backend; & C:\Users\onofr\Desktop\galia-app\backend\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider <archivos>`.
- **Encoding:** los archivos son UTF-8 con acentos. Editar con Edit/Write; nunca con PowerShell `Get-Content`/`Set-Content`.
- **Línea base:** `main` ya trae fallas. Comparar siempre con `backend/scripts/compare_baseline.py` contra `docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt`. Criterio: `Sin fallas nuevas.`
- **Commits:** terminan con la línea de atribución que pida el harness.
- **Tests:** SQLite en memoria. `with_for_update()` no hace nada en SQLite; la concurrencia real se prueba en la Task 15 con PostgreSQL.

## Mapa de archivos

**Nuevos**
- `backend/app/models/pos/__init__.py`, `floor.py`, `modifiers.py`, `payments.py`, `discounts.py`, `sale.py`, `events.py`
- `backend/app/services/pos/__init__.py`, `errors.py`, `pricing.py`, `audit.py`, `stock_hooks.py`, `common.py`, `serializers.py`, `projection.py`, `sale_service.py`, `discount_service.py`, `payment_service.py`
- `backend/app/routes/pos_sales.py`, `pos_floor.py`, `pos_config.py`
- `backend/migrations/versions/b1a4_add_pos_sales_engine.py`
- Tests: `backend/tests/pos_helpers.py`, `test_module_required_any.py`, `test_stock_moves.py`, `test_pos_models.py`, `test_pos_pricing.py`, `test_pos_open_items.py`, `test_pos_batches.py`, `test_pos_discounts.py`, `test_pos_payments.py`, `test_pos_cancellations.py`, `test_pos_move_split.py`, `test_pos_config_api.py`, `test_pos_sales_api.py`, `test_pos_concurrency_pg.py`

**Modificados**
- `backend/app/utils/decorators.py` — `module_required(*modules)`.
- `backend/app/services/stock_service.py` — `stock_requirements`, `move_stock` (con bloqueo y modo `allow_negative`).
- `backend/app/models/sale.py` — columna `source`.
- `backend/app/models/__init__.py`, `backend/app/__init__.py` — registrar modelos y blueprints.
- `backend/tests/test_migration_chain.py`.

---

### Task 1: `module_required` con varios módulos

**Files:**
- Modify: `backend/app/utils/decorators.py`
- Test: `backend/tests/test_module_required_any.py`

- [ ] **Step 1: Test que falla** — `backend/tests/test_module_required_any.py`:

```python
import pytest
from flask import jsonify

from app import create_app
from app.extensions import db
from app.models import Module, User, UserPermission
from app.utils.decorators import module_required


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _user_with(modules):
    user = User(email='u@test.com', role='employee', is_active=True)
    user.set_password('secret123')
    db.session.add(user)
    db.session.flush()
    for name in modules:
        module = Module(name=name, display_name=name, is_active=True)
        db.session.add(module)
        db.session.flush()
        db.session.add(UserPermission(user_id=user.id, module_id=module.id, is_granted=True))
    db.session.commit()
    return user


@module_required('POS', 'Camarero')
def _view(current_user):
    return jsonify({'ok': True}), 200


def test_any_of_the_modules_grants_access(app):
    user = _user_with(['Camarero'])
    with app.test_request_context('/x'):
        _response, status = _view(user)
    assert status == 200


def test_none_of_the_modules_is_403_naming_both(app):
    user = _user_with([])
    with app.test_request_context('/x'):
        response, status = _view(user)
    assert status == 403
    assert response.get_json()['message'] == 'No tienes acceso al módulo POS o Camarero'


def test_marks_all_modules():
    assert _view._access_control == 'module:POS|Camarero'


def test_requires_at_least_one_module():
    with pytest.raises(ValueError):
        module_required()
```

- [ ] **Step 2: Correr y ver que falla**

`PY -m pytest -q -p no:cacheprovider tests/test_module_required_any.py` (cwd `backend/`). Esperado: FAIL (`TypeError` por los dos argumentos).

- [ ] **Step 3: Implementar** — en `backend/app/utils/decorators.py`, reemplazar la función `module_required` completa por:

```python
def module_required(*module_names):
    """Exige acceso a alguno de los módulos indicados (admin siempre pasa). Va debajo de @token_required."""
    if not module_names:
        raise ValueError('module_required necesita al menos un módulo')
    label = ' o '.join(module_names)

    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if not current_user:
                logger.warning(
                    f"[SECURITY] Unauthorized access attempt | "
                    f"Path: {request.path} | Method: {request.method} | "
                    f"IP: {request.remote_addr} | Time: {datetime.utcnow().isoformat()}"
                )
                return jsonify({'error': 'Autenticación requerida'}), 401

            if not any(check_module_access(current_user, name) for name in module_names):
                logger.warning(
                    f"[SECURITY] Forbidden access attempt | "
                    f"User: {current_user.email} | Role: {current_user.role} | "
                    f"Required module: {label} | "
                    f"Path: {request.path} | Method: {request.method} | "
                    f"IP: {request.remote_addr} | Time: {datetime.utcnow().isoformat()}"
                )
                return jsonify({
                    'error': 'Acceso denegado',
                    'message': f'No tienes acceso al módulo {label}'
                }), 403

            return f(current_user, *args, **kwargs)
        decorated_function._access_control = 'module:' + '|'.join(module_names)
        return decorated_function
    return decorator
```

- [ ] **Step 4: Correr** `tests/test_module_required_any.py tests/test_access_control.py tests/test_route_access_coverage.py`. Esperado: todos pasan (el uso con un solo módulo no cambia).

- [ ] **Step 5: Commit**

```bash
git add backend/app/utils/decorators.py backend/tests/test_module_required_any.py
git commit -m "feat(permissions): allow module_required to accept any of several modules"
```

---

### Task 2: Movimientos de stock con bloqueo y modo sin bloqueo de venta

**Files:**
- Modify: `backend/app/services/stock_service.py`
- Test: `backend/tests/test_stock_moves.py`

- [ ] **Step 1: Test que falla** — `backend/tests/test_stock_moves.py`:

```python
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models import Product, ProductCategory, ProductRecipeItem, ProductVariant, Supply
from app.services.stock_service import deduct_stock_for_sale, move_stock, stock_requirements


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _setup():
    cat = ProductCategory(name='Cafés')
    db.session.add(cat)
    db.session.flush()
    cafe = Supply(name='Café', unit='kg', stock_quantity=Decimal('1'), min_stock=0)
    db.session.add(cafe)
    simple = Product(name='Medialuna', category_id=cat.id, has_recipe=False, track_stock=True)
    untracked = Product(name='Agua', category_id=cat.id, has_recipe=False, track_stock=False)
    recipe = Product(name='Cortado', category_id=cat.id, has_recipe=True)
    db.session.add_all([simple, untracked, recipe])
    db.session.flush()
    db.session.add(ProductRecipeItem(product_id=recipe.id, supply_id=cafe.id, quantity=Decimal('0.02'), unit='kg'))
    v_simple = ProductVariant(product_id=simple.id, name='Unidad', price=900, stock_quantity=Decimal('2'), min_stock=0)
    v_untracked = ProductVariant(product_id=untracked.id, name='Botella', price=1000, stock_quantity=0, min_stock=0)
    v_recipe = ProductVariant(product_id=recipe.id, name='Taza', price=2000, stock_quantity=0, min_stock=0)
    db.session.add_all([v_simple, v_untracked, v_recipe])
    db.session.commit()
    return cafe, v_simple, v_untracked, v_recipe


def test_requirements_split_variants_and_supplies(app):
    cafe, v_simple, v_untracked, v_recipe = _setup()
    variants, supplies = stock_requirements(
        {v_simple.id: Decimal('3'), v_untracked.id: Decimal('1'), v_recipe.id: Decimal('5')},
        extra_supplies={cafe.id: Decimal('0.1')},
    )
    assert variants == {v_simple.id: Decimal('3')}
    assert supplies == {cafe.id: Decimal('0.2')}


def test_unknown_variant_raises(app):
    with pytest.raises(ValueError, match='no encontrado'):
        stock_requirements({999: Decimal('1')})


def test_move_stock_allows_negative_when_asked(app):
    cafe, v_simple, _u, _r = _setup()
    move_stock({v_simple.id: Decimal('3')}, {cafe.id: Decimal('2')}, sign=-1, allow_negative=True)
    db.session.commit()
    assert Decimal(db.session.get(ProductVariant, v_simple.id).stock_quantity) == Decimal('-1')
    assert Decimal(db.session.get(Supply, cafe.id).stock_quantity) == Decimal('-1')


def test_move_stock_validates_by_default(app):
    _cafe, v_simple, _u, _r = _setup()
    with pytest.raises(ValueError, match='Stock insuficiente'):
        move_stock({v_simple.id: Decimal('3')}, {}, sign=-1)
    assert Decimal(db.session.get(ProductVariant, v_simple.id).stock_quantity) == Decimal('2')


def test_move_stock_restores(app):
    cafe, v_simple, _u, _r = _setup()
    move_stock({v_simple.id: Decimal('1')}, {cafe.id: Decimal('0.5')}, sign=1)
    db.session.commit()
    assert Decimal(db.session.get(ProductVariant, v_simple.id).stock_quantity) == Decimal('3')
    assert Decimal(db.session.get(Supply, cafe.id).stock_quantity) == Decimal('1.5')


def test_deduct_stock_for_sale_keeps_its_behavior(app):
    cafe, v_simple, _u, v_recipe = _setup()
    deduct_stock_for_sale([{'product_variant_id': v_simple.id, 'quantity': 2},
                           {'product_variant_id': v_recipe.id, 'quantity': 10}])
    db.session.commit()
    assert Decimal(db.session.get(ProductVariant, v_simple.id).stock_quantity) == Decimal('0')
    assert Decimal(db.session.get(Supply, cafe.id).stock_quantity) == Decimal('0.8')
    with pytest.raises(ValueError, match='Stock insuficiente'):
        deduct_stock_for_sale([{'product_variant_id': v_simple.id, 'quantity': 1}])
```

- [ ] **Step 2: Correr y ver que falla** (`ImportError` de `move_stock`).

- [ ] **Step 3: Implementar** — en `backend/app/services/stock_service.py`:

1. Reemplazar el docstring final y el bloque desde `variant_deductions = []  # (variant, cantidad)` hasta el final de `deduct_stock_for_sale` (incluido `db.session.flush()`) por:

```python
    variants, supplies = stock_requirements(dict(variant_needed))
    move_stock(variants, supplies, sign=-1)
```

y en el docstring de `deduct_stock_for_sale` reemplazar el párrafo `NOTA: no hay bloqueo de filas...` por:

```
    Las filas se bloquean con SELECT ... FOR UPDATE (ver move_stock).
```

2. Agregar al final del archivo:

```python
def stock_requirements(variant_quantities, extra_supplies=None):
    """Calcula qué stock hay que mover para estas cantidades vendidas.

    variant_quantities: {product_variant_id: Decimal}; extra_supplies: {supply_id: Decimal}
    (por ejemplo, insumos de modificadores). Devuelve (variantes, insumos) como {id: Decimal}:
    - producto con receta: insumos de la receta × cantidad;
    - producto sin receta con track_stock: la propia variante;
    - producto sin receta sin track_stock: nada.
    Levanta ValueError si una variante no existe.
    """
    variants = defaultdict(Decimal)
    supplies = defaultdict(Decimal)
    for variant_id, quantity in variant_quantities.items():
        variant = db.session.get(ProductVariant, variant_id)
        if not variant:
            raise ValueError(f'ProductVariant {variant_id} no encontrado')
        product = variant.product
        if product.has_recipe:
            for recipe_item in ProductRecipeItem.query.filter_by(product_id=product.id).all():
                supplies[recipe_item.supply_id] += Decimal(recipe_item.quantity) * quantity
        elif product.track_stock:
            variants[variant_id] += quantity
    for supply_id, quantity in (extra_supplies or {}).items():
        supplies[supply_id] += quantity
    return dict(variants), dict(supplies)


def move_stock(variants, supplies, sign, allow_negative=False):
    """Aplica un movimiento de stock: sign=-1 descuenta, sign=1 devuelve.

    Bloquea las filas con SELECT ... FOR UPDATE en orden de id (evita deadlocks) y recarga
    sus valores. Con sign=-1 y allow_negative=False valida que alcance y, si falta, no
    modifica nada. El llamador hace commit o rollback.
    """
    if sign not in (-1, 1):
        raise ValueError('sign debe ser -1 o 1')
    locked_variants = (
        ProductVariant.query.filter(ProductVariant.id.in_(list(variants)))
        .order_by(ProductVariant.id).with_for_update().populate_existing().all()
        if variants else []
    )
    locked_supplies = (
        Supply.query.filter(Supply.id.in_(list(supplies)))
        .order_by(Supply.id).with_for_update().populate_existing().all()
        if supplies else []
    )
    if len(locked_variants) != len(variants) or len(locked_supplies) != len(supplies):
        raise ValueError('Producto o insumo no encontrado')
    if sign < 0 and not allow_negative:
        for variant in locked_variants:
            if Decimal(variant.stock_quantity) < variants[variant.id]:
                raise ValueError(f'Stock insuficiente para {variant.product.name} - {variant.name}')
        for supply in locked_supplies:
            if Decimal(supply.stock_quantity) < supplies[supply.id]:
                raise ValueError(f'Stock insuficiente de {supply.name}')
    for variant in locked_variants:
        variant.stock_quantity = Decimal(variant.stock_quantity) + sign * variants[variant.id]
    for supply in locked_supplies:
        supply.stock_quantity = Decimal(supply.stock_quantity) + sign * supplies[supply.id]
    db.session.flush()
```

- [ ] **Step 4: Correr** `tests/test_stock_moves.py tests/test_stock_service.py tests/test_products.py`. Esperado: todos pasan.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/stock_service.py backend/tests/test_stock_moves.py
git commit -m "feat(stock): add locked stock moves with optional negative stock"
```

---

### Task 3: Modelos de configuración y `sales.source`

**Files:**
- Create: `backend/app/models/pos/__init__.py`, `floor.py`, `modifiers.py`, `payments.py`, `discounts.py`
- Modify: `backend/app/models/sale.py`, `backend/app/models/__init__.py`
- Test: `backend/tests/test_pos_models.py`

Esta task crea solo la configuración (salones, mesas, modificadores, medios de pago, plantillas). `payments.py` y `discounts.py` incluyen ya `PosPayment` y `PosDiscount`, que referencian `pos_sales`; esas clases se completan en la Task 4 junto con `sale.py`. Para que esta task quede sana por sí sola, `payments.py` y `discounts.py` se crean ahora **solo con las clases de configuración**, y la Task 4 les agrega las de venta.

- [ ] **Step 1: Test que falla** — `backend/tests/test_pos_models.py`:

```python
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models import Product, ProductCategory, Sale, Supply
from app.models.pos import (DiscountTemplate, ModifierGroup, ModifierOption, PaymentMethod,
                            PosTable, ProductModifierGroup, Salon)


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_floor_and_table_label(app):
    salon = Salon(name='Salón')
    db.session.add(salon)
    db.session.flush()
    table = PosTable(salon_id=salon.id, number=4)
    named = PosTable(salon_id=salon.id, number=5, name='Barra')
    db.session.add_all([table, named])
    db.session.commit()
    assert table.label == 'Mesa 4'
    assert named.label == 'Barra'
    assert [t.number for t in salon.tables] == [4, 5]
    assert table.to_dict()['salon_id'] == salon.id


def test_modifier_group_with_options(app):
    supply = Supply(name='Leche de almendras', unit='L', stock_quantity=1, min_stock=0)
    cat = ProductCategory(name='Cafés')
    db.session.add_all([supply, cat])
    db.session.flush()
    product = Product(name='Cortado', category_id=cat.id)
    group = ModifierGroup(name='Tipo de leche', min_select=1, max_select=1)
    db.session.add_all([product, group])
    db.session.flush()
    db.session.add_all([
        ModifierOption(group_id=group.id, name='Almendras', price_delta=Decimal('300'), supply_id=supply.id,
                       supply_quantity=Decimal('0.2'), position=1),
        ModifierOption(group_id=group.id, name='Entera', price_delta=0, position=0),
        ProductModifierGroup(product_id=product.id, group_id=group.id, position=0),
    ])
    db.session.commit()
    data = group.to_dict()
    assert [o['name'] for o in data['options']] == ['Entera', 'Almendras']
    assert data['options'][1]['supply_name'] == 'Leche de almendras'


def test_payment_method_and_template(app):
    db.session.add_all([
        PaymentMethod(name='Efectivo', kind='cash'),
        DiscountTemplate(name='Empleado', kind='percent', value=Decimal('20'), scope='sale', restricted=True),
    ])
    db.session.commit()
    assert PaymentMethod.query.one().to_dict()['kind'] == 'cash'
    assert DiscountTemplate.query.one().to_dict()['restricted'] is True


def test_sales_source_defaults_to_fudo(app):
    from datetime import date, datetime
    sale = Sale(fecha=date.today(), creacion=datetime.utcnow(), total=0)
    db.session.add(sale)
    db.session.commit()
    assert sale.source == 'fudo'
    assert sale.to_dict()['source'] == 'fudo'
```

- [ ] **Step 2: Correr y ver que falla** (`ModuleNotFoundError: app.models.pos`).

- [ ] **Step 3: Crear los modelos**

`backend/app/models/pos/floor.py`:

```python
from datetime import datetime

from app.extensions import db


class Salon(db.Model):
    __tablename__ = 'salons'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    tables = db.relationship('PosTable', back_populates='salon', order_by='PosTable.number')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'position': self.position, 'is_active': self.is_active}


class PosTable(db.Model):
    __tablename__ = 'pos_tables'
    __table_args__ = (db.UniqueConstraint('salon_id', 'number', name='uq_pos_tables_salon_number'),)

    id = db.Column(db.Integer, primary_key=True)
    salon_id = db.Column(db.Integer, db.ForeignKey('salons.id'), nullable=False, index=True)
    number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(50), nullable=True)
    capacity = db.Column(db.Integer, nullable=True)
    pos_x = db.Column(db.Float, nullable=False, default=10.0)
    pos_y = db.Column(db.Float, nullable=False, default=10.0)
    width = db.Column(db.Float, nullable=False, default=10.0)
    height = db.Column(db.Float, nullable=False, default=10.0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    salon = db.relationship('Salon', back_populates='tables')

    @property
    def label(self):
        return self.name or f'Mesa {self.number}'

    def to_dict(self):
        return {
            'id': self.id,
            'salon_id': self.salon_id,
            'number': self.number,
            'name': self.name,
            'label': self.label,
            'capacity': self.capacity,
            'pos_x': self.pos_x,
            'pos_y': self.pos_y,
            'width': self.width,
            'height': self.height,
            'is_active': self.is_active,
        }
```

`backend/app/models/pos/modifiers.py`:

```python
from datetime import datetime

from app.extensions import db


class ModifierGroup(db.Model):
    __tablename__ = 'modifier_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    min_select = db.Column(db.Integer, nullable=False, default=0)
    max_select = db.Column(db.Integer, nullable=False, default=1)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    options = db.relationship('ModifierOption', back_populates='group',
                              order_by='[ModifierOption.position, ModifierOption.id]')

    def to_dict(self, include_inactive=False):
        return {
            'id': self.id,
            'name': self.name,
            'min_select': self.min_select,
            'max_select': self.max_select,
            'is_active': self.is_active,
            'options': [o.to_dict() for o in self.options if include_inactive or o.is_active],
        }


class ModifierOption(db.Model):
    __tablename__ = 'modifier_options'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('modifier_groups.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    price_delta = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    supply_id = db.Column(db.Integer, db.ForeignKey('supplies.id'), nullable=True)
    supply_quantity = db.Column(db.Numeric(10, 4), nullable=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    group = db.relationship('ModifierGroup', back_populates='options')
    supply = db.relationship('Supply')

    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'name': self.name,
            'price_delta': float(self.price_delta),
            'supply_id': self.supply_id,
            'supply_name': self.supply.name if self.supply else None,
            'supply_quantity': float(self.supply_quantity) if self.supply_quantity is not None else None,
            'position': self.position,
            'is_active': self.is_active,
        }


class ProductModifierGroup(db.Model):
    __tablename__ = 'product_modifier_groups'

    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('modifier_groups.id'), primary_key=True)
    position = db.Column(db.Integer, nullable=False, default=0)

    group = db.relationship('ModifierGroup')
```

`backend/app/models/pos/payments.py` (por ahora solo el catálogo):

```python
from app.extensions import db

PAYMENT_KINDS = ('cash', 'card', 'transfer', 'other')


class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    kind = db.Column(db.String(20), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'kind': self.kind, 'position': self.position,
                'is_active': self.is_active}
```

`backend/app/models/pos/discounts.py` (por ahora solo las plantillas):

```python
from app.extensions import db

DISCOUNT_KINDS = ('percent', 'amount')
DISCOUNT_SCOPES = ('sale', 'item')


class DiscountTemplate(db.Model):
    __tablename__ = 'discount_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    kind = db.Column(db.String(10), nullable=False)
    value = db.Column(db.Numeric(10, 2), nullable=False)
    scope = db.Column(db.String(10), nullable=False)
    restricted = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'kind': self.kind, 'value': float(self.value),
                'scope': self.scope, 'restricted': self.restricted, 'is_active': self.is_active}
```

`backend/app/models/pos/__init__.py`:

```python
from app.models.pos.floor import PosTable, Salon
from app.models.pos.modifiers import ModifierGroup, ModifierOption, ProductModifierGroup
from app.models.pos.payments import PAYMENT_KINDS, PaymentMethod
from app.models.pos.discounts import DISCOUNT_KINDS, DISCOUNT_SCOPES, DiscountTemplate

__all__ = [
    'Salon', 'PosTable', 'ModifierGroup', 'ModifierOption', 'ProductModifierGroup',
    'PaymentMethod', 'PAYMENT_KINDS', 'DiscountTemplate', 'DISCOUNT_KINDS', 'DISCOUNT_SCOPES',
]
```

- [ ] **Step 4: `sales.source`** — en `backend/app/models/sale.py`, debajo de la columna `id_origen` agregar:

```python
    source = db.Column(db.String(20), nullable=False, default='fudo', server_default='fudo')
```

y en `Sale.to_dict()` agregar la clave `'source': self.source,` (después de `'id_origen'`).

- [ ] **Step 5: Registrar** — al final de los imports de `backend/app/models/__init__.py` agregar:

```python
from app.models.pos import (Salon, PosTable, ModifierGroup, ModifierOption, ProductModifierGroup,
                            PaymentMethod, DiscountTemplate)
```

y agregar esos siete nombres al final de `__all__`.

- [ ] **Step 6: Correr** `tests/test_pos_models.py tests/test_sales_date_filter.py`. Esperado: `test_pos_models.py` pasa entero; `test_sales_date_filter.py` igual que en la línea base.

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/pos backend/app/models/sale.py backend/app/models/__init__.py backend/tests/test_pos_models.py
git commit -m "feat(pos): add floor, modifier, payment method and discount template models"
```

---

### Task 4: Modelos de venta

**Files:**
- Create: `backend/app/models/pos/sale.py`, `backend/app/models/pos/events.py`
- Modify: `backend/app/models/pos/payments.py`, `backend/app/models/pos/discounts.py`, `backend/app/models/pos/__init__.py`, `backend/app/models/__init__.py`
- Test: `backend/tests/test_pos_models.py` (agregar)

- [ ] **Step 1: Test que falla** — agregar a `backend/tests/test_pos_models.py`:

```python
def test_sale_aggregate_relationships(app):
    from datetime import date, datetime
    from app.models import ProductVariant, User
    from app.models.pos import PosDiscount, PosPayment, PosSale, PosSaleEvent, PosSaleItem, PosSaleItemModifier

    user = User(email='u@test.com', role='admin', is_active=True)
    user.set_password('secret123')
    cat = ProductCategory(name='Cafés')
    db.session.add_all([user, cat])
    db.session.flush()
    product = Product(name='Cortado', category_id=cat.id)
    db.session.add(product)
    db.session.flush()
    variant = ProductVariant(product_id=product.id, name='Taza', price=2000, stock_quantity=0, min_stock=0)
    group = ModifierGroup(name='Leche', min_select=0, max_select=1)
    method = PaymentMethod(name='Efectivo', kind='cash')
    db.session.add_all([variant, group, method])
    db.session.flush()
    option = ModifierOption(group_id=group.id, name='Almendras', price_delta=300)
    db.session.add(option)
    db.session.flush()

    sale = PosSale(business_date=date.today(), number=1, sale_type='counter', status='open',
                   opened_at=datetime.utcnow(), opened_by=user.id)
    item = PosSaleItem(product_variant_id=variant.id, product_name='Cortado', variant_name='Taza',
                       unit_price=2000, quantity=1, modifiers_total=300, line_total=2300,
                       created_by=user.id, created_at=datetime.utcnow())
    item.modifiers.append(PosSaleItemModifier(option_id=option.id, group_name='Leche', option_name='Almendras',
                                              price_delta=300))
    sale.items.append(item)
    db.session.add(sale)
    db.session.flush()
    sale.discounts.append(PosDiscount(item=item, kind='amount', value=100, amount=100, created_by=user.id,
                                      created_at=datetime.utcnow()))
    sale.payments.append(PosPayment(payment_method_id=method.id, method_name='Efectivo', amount=2200,
                                    created_by=user.id, created_at=datetime.utcnow()))
    db.session.add(PosSaleEvent(sale_id=sale.id, user_id=user.id, event_type='opened', payload={'x': 1},
                                created_at=datetime.utcnow()))
    db.session.commit()

    assert item.status == 'pending'
    assert sale.items[0].modifiers[0].option_name == 'Almendras'
    assert sale.discounts[0].item is item and item.discounts[0].is_active
    assert sale.payments[0].is_active
    assert PosSaleEvent.query.one().payload == {'x': 1}
```

- [ ] **Step 2: Correr y ver que falla** (`ImportError: PosSale`).

- [ ] **Step 3: Crear `backend/app/models/pos/sale.py`**:

```python
from decimal import Decimal

from app.extensions import db

SALE_TYPES = ('salon', 'counter')
SALE_STATUSES = ('open', 'billing', 'closed', 'cancelled')
ACTIVE_SALE_STATUSES = ('open', 'billing')
ITEM_STATUSES = ('pending', 'confirmed', 'cancelled')


class PosSale(db.Model):
    __tablename__ = 'pos_sales'
    __table_args__ = (db.UniqueConstraint('business_date', 'number', name='uq_pos_sales_day_number'),)

    id = db.Column(db.Integer, primary_key=True)
    business_date = db.Column(db.Date, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    sale_type = db.Column(db.String(10), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('pos_tables.id'), nullable=True, index=True)
    people = db.Column(db.Integer, nullable=True)
    customer_name = db.Column(db.String(100), nullable=True)
    comment = db.Column(db.String(500), nullable=True)
    waiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(10), nullable=False, default='open', index=True)
    opened_at = db.Column(db.DateTime, nullable=False, index=True)
    opened_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    billing_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    closed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancel_reason = db.Column(db.String(255), nullable=True)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount_total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    paid_total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    split_from_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id', ondelete='SET NULL'), nullable=True)

    table = db.relationship('PosTable')
    waiter = db.relationship('User', foreign_keys=[waiter_id])
    items = db.relationship('PosSaleItem', back_populates='sale', order_by='PosSaleItem.id',
                            cascade='all, delete-orphan')
    discounts = db.relationship('PosDiscount', back_populates='sale', order_by='PosDiscount.id',
                                cascade='all, delete-orphan')
    payments = db.relationship('PosPayment', back_populates='sale', order_by='PosPayment.id',
                               cascade='all, delete-orphan')

    @property
    def balance(self):
        return Decimal(self.total or 0) - Decimal(self.paid_total or 0)


class PosSaleItem(db.Model):
    __tablename__ = 'pos_sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=False, index=True)
    product_variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    variant_name = db.Column(db.String(100), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    modifiers_total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    note = db.Column(db.String(255), nullable=True)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='pending')
    batch = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    confirmed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancel_reason = db.Column(db.String(255), nullable=True)

    sale = db.relationship('PosSale', back_populates='items')
    modifiers = db.relationship('PosSaleItemModifier', back_populates='item', order_by='PosSaleItemModifier.id',
                                cascade='all, delete-orphan')
    discounts = db.relationship('PosDiscount', back_populates='item', order_by='PosDiscount.id')


class PosSaleItemModifier(db.Model):
    __tablename__ = 'pos_sale_item_modifiers'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('pos_sale_items.id'), nullable=False, index=True)
    option_id = db.Column(db.Integer, db.ForeignKey('modifier_options.id'), nullable=False)
    group_name = db.Column(db.String(100), nullable=False)
    option_name = db.Column(db.String(100), nullable=False)
    price_delta = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    supply_id = db.Column(db.Integer, db.ForeignKey('supplies.id'), nullable=True)
    supply_quantity = db.Column(db.Numeric(10, 4), nullable=True)

    item = db.relationship('PosSaleItem', back_populates='modifiers')
```

- [ ] **Step 4: Crear `backend/app/models/pos/events.py`**:

```python
from app.extensions import db


class PosSaleEvent(db.Model):
    __tablename__ = 'pos_sale_events'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=False, index=True)
    item_id = db.Column(db.Integer, nullable=True)  # sin FK: los ítems pendientes borrados conservan su evento
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_type = db.Column(db.String(30), nullable=False)
    payload = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, index=True)

    def to_dict(self):
        return {'id': self.id, 'sale_id': self.sale_id, 'item_id': self.item_id, 'user_id': self.user_id,
                'event_type': self.event_type, 'payload': self.payload, 'created_at': self.created_at.isoformat()}
```

- [ ] **Step 5: Agregar `PosPayment` y `PosDiscount`**

Al final de `backend/app/models/pos/payments.py`:

```python


class PosPayment(db.Model):
    __tablename__ = 'pos_payments'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=False, index=True)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'), nullable=False)
    method_name = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    tendered = db.Column(db.Numeric(12, 2), nullable=True)
    change = db.Column(db.Numeric(12, 2), nullable=True)
    client_request_id = db.Column(db.String(64), nullable=True, unique=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancel_reason = db.Column(db.String(255), nullable=True)

    sale = db.relationship('PosSale', back_populates='payments')

    @property
    def is_active(self):
        return self.cancelled_at is None
```

Al final de `backend/app/models/pos/discounts.py`:

```python


class PosDiscount(db.Model):
    __tablename__ = 'pos_discounts'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey('pos_sale_items.id'), nullable=True, index=True)
    template_id = db.Column(db.Integer, db.ForeignKey('discount_templates.id'), nullable=True)
    kind = db.Column(db.String(10), nullable=False)
    value = db.Column(db.Numeric(10, 2), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    reason = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    sale = db.relationship('PosSale', back_populates='discounts')
    item = db.relationship('PosSaleItem', back_populates='discounts')
    template = db.relationship('DiscountTemplate')

    @property
    def is_active(self):
        return self.cancelled_at is None
```

- [ ] **Step 6: Exportar** — reemplazar `backend/app/models/pos/__init__.py` por:

```python
from app.models.pos.floor import PosTable, Salon
from app.models.pos.modifiers import ModifierGroup, ModifierOption, ProductModifierGroup
from app.models.pos.payments import PAYMENT_KINDS, PaymentMethod, PosPayment
from app.models.pos.discounts import DISCOUNT_KINDS, DISCOUNT_SCOPES, DiscountTemplate, PosDiscount
from app.models.pos.sale import (ACTIVE_SALE_STATUSES, ITEM_STATUSES, SALE_STATUSES, SALE_TYPES, PosSale,
                                 PosSaleItem, PosSaleItemModifier)
from app.models.pos.events import PosSaleEvent

__all__ = [
    'Salon', 'PosTable', 'ModifierGroup', 'ModifierOption', 'ProductModifierGroup',
    'PaymentMethod', 'PAYMENT_KINDS', 'PosPayment',
    'DiscountTemplate', 'DISCOUNT_KINDS', 'DISCOUNT_SCOPES', 'PosDiscount',
    'PosSale', 'PosSaleItem', 'PosSaleItemModifier', 'SALE_TYPES', 'SALE_STATUSES', 'ACTIVE_SALE_STATUSES',
    'ITEM_STATUSES', 'PosSaleEvent',
]
```

y en `backend/app/models/__init__.py` ampliar el import de `app.models.pos` con `PosPayment, PosDiscount, PosSale, PosSaleItem, PosSaleItemModifier, PosSaleEvent`, agregándolos también a `__all__`.

- [ ] **Step 7: Correr** `tests/test_pos_models.py`. Esperado: 5 passed.

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/pos backend/app/models/__init__.py backend/tests/test_pos_models.py
git commit -m "feat(pos): add sale, item, discount, payment and audit event models"
```

---

### Task 5: Migración `b1a4_add_pos_sales_engine`

**Files:**
- Create: `backend/migrations/versions/b1a4_add_pos_sales_engine.py`
- Modify: `backend/tests/test_migration_chain.py`

- [ ] **Step 1: Test que falla** — agregar a `backend/tests/test_migration_chain.py`:

```python


def test_pos_sales_engine_is_head():
    assert _revisions()['b1a4_add_pos_sales_engine'] == ['b1a3_add_site_config']
```

- [ ] **Step 2: Correr** `tests/test_migration_chain.py`. Esperado: FAIL (`KeyError`).

- [ ] **Step 3: Crear la migración** — `backend/migrations/versions/b1a4_add_pos_sales_engine.py`:

```python
"""add POS sales engine tables, sales.source, POS modules and payment methods

Revision ID: b1a4_add_pos_sales_engine
Revises: b1a3_add_site_config
Create Date: 2026-10-09 00:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = 'b1a4_add_pos_sales_engine'
down_revision = 'b1a3_add_site_config'
branch_labels = None
depends_on = None

POS_MODULES = [
    ('POS', 'Caja (POS)', 'Plano de mesas, ventas, mostrador, cobro y configuración de salones', '/pos'),
    ('Camarero', 'Camarero', 'Abrir mesas, cargar pedidos y pedir la cuenta', '/camarero'),
    ('Cobrar', 'Cobrar', 'Registrar pagos y cerrar ventas', None),
    ('Anular', 'Anular', 'Anular ítems confirmados, pagos y ventas', None),
    ('Descuentos', 'Descuentos', 'Descuentos libres y plantillas restringidas', None),
]
PAYMENT_METHODS = [
    ('Efectivo', 'cash', 0), ('Débito', 'card', 1), ('Crédito', 'card', 2),
    ('Transferencia', 'transfer', 3), ('MercadoPago', 'other', 4),
]


def _timestamps():
    return [
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    ]


def upgrade():
    op.create_table(
        'salons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'pos_tables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('salon_id', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('pos_x', sa.Float(), nullable=False, server_default='10'),
        sa.Column('pos_y', sa.Float(), nullable=False, server_default='10'),
        sa.Column('width', sa.Float(), nullable=False, server_default='10'),
        sa.Column('height', sa.Float(), nullable=False, server_default='10'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        sa.ForeignKeyConstraint(['salon_id'], ['salons.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('salon_id', 'number', name='uq_pos_tables_salon_number'),
    )
    op.create_index(op.f('ix_pos_tables_salon_id'), 'pos_tables', ['salon_id'])
    op.create_table(
        'modifier_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('min_select', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_select', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'modifier_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('price_delta', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('supply_id', sa.Integer(), nullable=True),
        sa.Column('supply_quantity', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(['group_id'], ['modifier_groups.id']),
        sa.ForeignKeyConstraint(['supply_id'], ['supplies.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_modifier_options_group_id'), 'modifier_options', ['group_id'])
    op.create_table(
        'product_modifier_groups',
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['group_id'], ['modifier_groups.id']),
        sa.PrimaryKeyConstraint('product_id', 'group_id'),
    )
    payment_methods = op.create_table(
        'payment_methods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'discount_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('value', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('scope', sa.String(length=10), nullable=False),
        sa.Column('restricted', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'pos_sales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_date', sa.Date(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('sale_type', sa.String(length=10), nullable=False),
        sa.Column('table_id', sa.Integer(), nullable=True),
        sa.Column('people', sa.Integer(), nullable=True),
        sa.Column('customer_name', sa.String(length=100), nullable=True),
        sa.Column('comment', sa.String(length=500), nullable=True),
        sa.Column('waiter_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=10), nullable=False, server_default='open'),
        sa.Column('opened_at', sa.DateTime(), nullable=False),
        sa.Column('opened_by', sa.Integer(), nullable=False),
        sa.Column('billing_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_by', sa.Integer(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_by', sa.Integer(), nullable=True),
        sa.Column('cancel_reason', sa.String(length=255), nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('discount_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('paid_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('split_from_id', sa.Integer(), nullable=True),
        sa.Column('sale_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['table_id'], ['pos_tables.id']),
        sa.ForeignKeyConstraint(['waiter_id'], ['users.id']),
        sa.ForeignKeyConstraint(['opened_by'], ['users.id']),
        sa.ForeignKeyConstraint(['closed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['cancelled_by'], ['users.id']),
        sa.ForeignKeyConstraint(['split_from_id'], ['pos_sales.id']),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('business_date', 'number', name='uq_pos_sales_day_number'),
    )
    op.create_index(op.f('ix_pos_sales_table_id'), 'pos_sales', ['table_id'])
    op.create_index(op.f('ix_pos_sales_status'), 'pos_sales', ['status'])
    op.create_index(op.f('ix_pos_sales_opened_at'), 'pos_sales', ['opened_at'])
    op.create_table(
        'pos_sale_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('product_variant_id', sa.Integer(), nullable=False),
        sa.Column('product_name', sa.String(length=200), nullable=False),
        sa.Column('variant_name', sa.String(length=100), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('modifiers_total', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('line_total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False, server_default='pending'),
        sa.Column('batch', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('confirmed_by', sa.Integer(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_by', sa.Integer(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancel_reason', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['sale_id'], ['pos_sales.id']),
        sa.ForeignKeyConstraint(['product_variant_id'], ['product_variants.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['confirmed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['cancelled_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pos_sale_items_sale_id'), 'pos_sale_items', ['sale_id'])
    op.create_table(
        'pos_sale_item_modifiers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('option_id', sa.Integer(), nullable=False),
        sa.Column('group_name', sa.String(length=100), nullable=False),
        sa.Column('option_name', sa.String(length=100), nullable=False),
        sa.Column('price_delta', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('supply_id', sa.Integer(), nullable=True),
        sa.Column('supply_quantity', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['pos_sale_items.id']),
        sa.ForeignKeyConstraint(['option_id'], ['modifier_options.id']),
        sa.ForeignKeyConstraint(['supply_id'], ['supplies.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pos_sale_item_modifiers_item_id'), 'pos_sale_item_modifiers', ['item_id'])
    op.create_table(
        'pos_discounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('value', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('cancelled_by', sa.Integer(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['sale_id'], ['pos_sales.id']),
        sa.ForeignKeyConstraint(['item_id'], ['pos_sale_items.id']),
        sa.ForeignKeyConstraint(['template_id'], ['discount_templates.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['cancelled_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pos_discounts_sale_id'), 'pos_discounts', ['sale_id'])
    op.create_index(op.f('ix_pos_discounts_item_id'), 'pos_discounts', ['item_id'])
    op.create_table(
        'pos_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('payment_method_id', sa.Integer(), nullable=False),
        sa.Column('method_name', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('tendered', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('change', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('client_request_id', sa.String(length=64), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('cancelled_by', sa.Integer(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancel_reason', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['sale_id'], ['pos_sales.id']),
        sa.ForeignKeyConstraint(['payment_method_id'], ['payment_methods.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['cancelled_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_request_id'),
    )
    op.create_index(op.f('ix_pos_payments_sale_id'), 'pos_payments', ['sale_id'])
    op.create_table(
        'pos_sale_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=30), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['sale_id'], ['pos_sales.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pos_sale_events_sale_id'), 'pos_sale_events', ['sale_id'])
    op.create_index(op.f('ix_pos_sale_events_created_at'), 'pos_sale_events', ['created_at'])

    with op.batch_alter_table('sales') as batch:
        batch.add_column(sa.Column('source', sa.String(length=20), nullable=False, server_default='fudo'))

    now = datetime.utcnow()
    modules = sa.table('modules', sa.column('name', sa.String), sa.column('display_name', sa.String),
                       sa.column('description', sa.Text), sa.column('icon', sa.String),
                       sa.column('category', sa.String), sa.column('route', sa.String),
                       sa.column('is_active', sa.Boolean), sa.column('created_at', sa.DateTime),
                       sa.column('updated_at', sa.DateTime))
    op.bulk_insert(modules, [
        {'name': name, 'display_name': display, 'description': description, 'icon': None,
         'category': 'Operations', 'route': route, 'is_active': True, 'created_at': now, 'updated_at': now}
        for name, display, description, route in POS_MODULES
    ])
    names = [m[0] for m in POS_MODULES]
    rows = op.get_bind().execute(
        sa.text('SELECT id FROM modules WHERE name IN :names').bindparams(sa.bindparam('names', expanding=True)),
        {'names': names},
    ).fetchall()
    role_permissions = sa.table('role_permissions', sa.column('role', sa.String), sa.column('module_id', sa.Integer),
                                sa.column('is_granted', sa.Boolean), sa.column('created_at', sa.DateTime),
                                sa.column('updated_at', sa.DateTime))
    grants = []
    for (module_id,) in rows:
        grants.append({'role': 'admin', 'module_id': module_id, 'is_granted': True, 'created_at': now, 'updated_at': now})
        grants.append({'role': 'employee', 'module_id': module_id, 'is_granted': False, 'created_at': now,
                       'updated_at': now})
    op.bulk_insert(role_permissions, grants)
    op.bulk_insert(payment_methods, [
        {'name': name, 'kind': kind, 'position': position, 'is_active': True}
        for name, kind, position in PAYMENT_METHODS
    ])


def downgrade():
    bind = op.get_bind()
    names_param = sa.bindparam('names', expanding=True)
    names = {'names': [m[0] for m in POS_MODULES]}
    bind.execute(sa.text('DELETE FROM user_permissions WHERE module_id IN '
                         '(SELECT id FROM modules WHERE name IN :names)').bindparams(names_param), names)
    bind.execute(sa.text('DELETE FROM role_permissions WHERE module_id IN '
                         '(SELECT id FROM modules WHERE name IN :names)').bindparams(names_param), names)
    bind.execute(sa.text('DELETE FROM modules WHERE name IN :names').bindparams(names_param), names)

    with op.batch_alter_table('sales') as batch:
        batch.drop_column('source')

    for index, table in [
        ('ix_pos_sale_events_created_at', 'pos_sale_events'), ('ix_pos_sale_events_sale_id', 'pos_sale_events'),
        ('ix_pos_payments_sale_id', 'pos_payments'), ('ix_pos_discounts_item_id', 'pos_discounts'),
        ('ix_pos_discounts_sale_id', 'pos_discounts'),
        ('ix_pos_sale_item_modifiers_item_id', 'pos_sale_item_modifiers'),
        ('ix_pos_sale_items_sale_id', 'pos_sale_items'), ('ix_pos_sales_opened_at', 'pos_sales'),
        ('ix_pos_sales_status', 'pos_sales'), ('ix_pos_sales_table_id', 'pos_sales'),
        ('ix_modifier_options_group_id', 'modifier_options'), ('ix_pos_tables_salon_id', 'pos_tables'),
    ]:
        op.drop_index(op.f(index), table_name=table)
    for table in ['pos_sale_events', 'pos_payments', 'pos_discounts', 'pos_sale_item_modifiers', 'pos_sale_items',
                  'pos_sales', 'discount_templates', 'payment_methods', 'product_modifier_groups',
                  'modifier_options', 'modifier_groups', 'pos_tables', 'salons']:
        op.drop_table(table)
```

- [ ] **Step 4: Verificar en SQLite** con el helper de migraciones del controlador (crea `users`, `expenses` y `supplies` mínimas). Si el helper no existe en tu entorno, saltear este paso y dejarlo para la Task 16 (PostgreSQL). Comando:

`PY C:/Users/onofr/AppData/Local/Temp/claude/C--Users-onofr-Desktop-galia-app/b0813cae-ffa0-4183-9896-255af955f1ea/scratchpad/run_migration.py backend/migrations/versions/b1a0_add_permissions_system.py backend/migrations/versions/b1a1_add_suppliers.py backend/migrations/versions/b1a2_add_products_and_supplies.py backend/migrations/versions/b1a3_add_site_config.py backend/migrations/versions/b1a4_add_pos_sales_engine.py`

El helper no crea `sales` ni `products`; si falla por esas tablas, verificar en la Task 16 con PostgreSQL (`flask db upgrade` desde cero) y anotarlo en el reporte.

- [ ] **Step 5: Correr** `tests/test_migration_chain.py`. Esperado: todos pasan (un solo head).

- [ ] **Step 6: Commit**

```bash
git add backend/migrations/versions/b1a4_add_pos_sales_engine.py backend/tests/test_migration_chain.py
git commit -m "feat(pos): add POS sales engine migration with modules and payment methods"
```

---

### Task 6: Cálculo de totales (`pricing.py`)

**Files:**
- Create: `backend/app/services/pos/__init__.py` (vacío), `backend/app/services/pos/pricing.py`
- Test: `backend/tests/test_pos_pricing.py`

- [ ] **Step 1: Test que falla** — `backend/tests/test_pos_pricing.py`:

```python
from decimal import Decimal as D

from app.services.pos.pricing import Disc, Line, compute, discount_amount, line_total, money, split_value


def test_money_rounds_half_up():
    assert money(D('10.005')) == D('10.01')
    assert money(D('10.004')) == D('10.00')


def test_line_total_includes_modifiers():
    assert line_total(D('2'), D('2000'), D('300')) == D('4600.00')
    assert line_total(D('1.5'), D('1000'), D('0')) == D('1500.00')


def test_discount_amount_percent_and_cap():
    assert discount_amount('percent', D('10'), base=D('1000'), cap=D('1000')) == D('100.00')
    assert discount_amount('amount', D('500'), base=D('300'), cap=D('300')) == D('300.00')
    assert discount_amount('percent', D('50'), base=D('1000'), cap=D('200')) == D('200.00')
    assert discount_amount('amount', D('10'), base=D('0'), cap=D('0')) == D('0.00')


def test_compute_without_discounts():
    totals = compute([Line(1, D('2300')), Line(2, D('900'))], [])
    assert (totals.subtotal, totals.discount_total, totals.total) == (D('3200.00'), D('0.00'), D('3200.00'))


def test_item_discount_then_sale_percent_on_remaining():
    lines = [Line(1, D('2000')), Line(2, D('1000'))]
    discounts = [Disc(10, 1, 'percent', D('50')), Disc(11, None, 'percent', D('10'))]
    totals = compute(lines, discounts)
    assert totals.amounts == {10: D('1000.00'), 11: D('200.00')}
    assert totals.total == D('1800.00')


def test_discounts_never_make_total_negative():
    totals = compute([Line(1, D('500'))], [Disc(1, None, 'amount', D('400')), Disc(2, None, 'amount', D('400'))])
    assert totals.amounts == {1: D('400.00'), 2: D('100.00')}
    assert totals.total == D('0.00')


def test_discount_on_missing_item_is_zero():
    totals = compute([Line(1, D('500'))], [Disc(1, 99, 'amount', D('100'))])
    assert totals.amounts == {1: D('0.00')}
    assert totals.total == D('500.00')


def test_split_value_proportional():
    assert split_value(D('100'), D('1'), D('3')) == D('33.33')
```

- [ ] **Step 2: Correr y ver que falla** (`ModuleNotFoundError`).

- [ ] **Step 3: Implementar** — `backend/app/services/pos/__init__.py` vacío y `backend/app/services/pos/pricing.py`:

```python
"""Cálculo de totales del POS. Funciones puras: sin base de datos, todo en Decimal."""
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal('0.01')
ZERO = Decimal('0.00')


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def line_total(quantity, unit_price, modifiers_total):
    return money(Decimal(quantity) * (Decimal(unit_price) + Decimal(modifiers_total)))


def discount_amount(kind, value, base, cap):
    """Monto de un descuento: porcentaje sobre `base` o monto fijo, nunca mayor que `cap`."""
    cap = money(max(Decimal(cap), ZERO))
    raw = Decimal(base) * Decimal(value) / Decimal(100) if kind == 'percent' else Decimal(value)
    return min(money(max(raw, ZERO)), cap)


def split_value(value, part, whole):
    """Parte proporcional de un monto fijo al dividir `part` de `whole` unidades."""
    return money(Decimal(value) * Decimal(part) / Decimal(whole))


@dataclass(frozen=True)
class Line:
    key: object
    total: Decimal


@dataclass(frozen=True)
class Disc:
    key: object
    item_key: object  # None = descuento sobre la venta
    kind: str
    value: Decimal


@dataclass
class Totals:
    subtotal: Decimal
    discount_total: Decimal
    total: Decimal
    amounts: dict = field(default_factory=dict)


def compute(lines, discounts):
    """Totales de una venta.

    lines: renglones activos (pendientes y confirmados). discounts: descuentos activos en orden
    de creación. Primero los de ítem (porcentaje sobre el renglón, tope en lo que le queda),
    después los de venta (porcentaje sobre el subtotal ya descontado por ítems, tope en lo que
    queda). Nada queda negativo.
    """
    line_totals = {line.key: money(line.total) for line in lines}
    subtotal = money(sum(line_totals.values(), ZERO))
    remaining = dict(line_totals)
    amounts = {}
    for disc in discounts:
        if disc.item_key is None:
            continue
        base = line_totals.get(disc.item_key, ZERO)
        cap = remaining.get(disc.item_key, ZERO)
        amount = discount_amount(disc.kind, disc.value, base, cap)
        amounts[disc.key] = amount
        if disc.item_key in remaining:
            remaining[disc.item_key] = cap - amount
    sale_base = money(sum(remaining.values(), ZERO))
    sale_remaining = sale_base
    for disc in discounts:
        if disc.item_key is not None:
            continue
        amount = discount_amount(disc.kind, disc.value, sale_base, sale_remaining)
        amounts[disc.key] = amount
        sale_remaining -= amount
    discount_total = money(sum(amounts.values(), ZERO))
    return Totals(subtotal=subtotal, discount_total=discount_total, total=subtotal - discount_total, amounts=amounts)
```

- [ ] **Step 4: Correr** `tests/test_pos_pricing.py`. Esperado: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pos/__init__.py backend/app/services/pos/pricing.py backend/tests/test_pos_pricing.py
git commit -m "feat(pos): add pure pricing functions for lines and discounts"
```

---

### Task 7: Base del servicio, apertura e ítems

**Files:**
- Create: `backend/app/services/pos/errors.py`, `audit.py`, `stock_hooks.py`, `common.py`, `serializers.py`, `sale_service.py`
- Create: `backend/tests/pos_helpers.py`
- Test: `backend/tests/test_pos_open_items.py`

- [ ] **Step 1: Helpers de test** — `backend/tests/pos_helpers.py`:

```python
"""Fixtures y fábricas compartidas por los tests del POS."""
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app import create_app
from app.extensions import db
from app.models import Module, Product, ProductCategory, ProductRecipeItem, ProductVariant, Supply, User, UserPermission
from app.models.pos import (DiscountTemplate, ModifierGroup, ModifierOption, PaymentMethod, PosTable,
                            ProductModifierGroup, Salon)

PASSWORD = 'secret123'


@pytest.fixture
def pos_app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def make_user(email, role='employee', modules=()):
    user = User(email=email, role=role, is_active=True)
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.flush()
    for name in modules:
        module = Module.query.filter_by(name=name).first()
        if module is None:
            module = Module(name=name, display_name=name, is_active=True)
            db.session.add(module)
            db.session.flush()
        db.session.add(UserPermission(user_id=user.id, module_id=module.id, is_granted=True))
    db.session.commit()
    return user


def auth_headers(client, user):
    response = client.post('/api/v1/auth/login', json={'email': user.email, 'password': PASSWORD})
    return {'Authorization': f"Bearer {response.get_json()['token']}"}


def make_floor():
    salon = Salon(name='Salón')
    db.session.add(salon)
    db.session.flush()
    t1 = PosTable(salon_id=salon.id, number=1)
    t2 = PosTable(salon_id=salon.id, number=2)
    db.session.add_all([t1, t2])
    db.session.commit()
    return salon, t1, t2


def make_catalog():
    """Cortado (receta: 0,02 kg de café; modificador obligatorio de leche) y Medialuna (stock 5)."""
    cat = ProductCategory(name='Cafetería')
    cafe = Supply(name='Café', unit='kg', stock_quantity=Decimal('1'), min_stock=0)
    almendras_supply = Supply(name='Leche de almendras', unit='L', stock_quantity=Decimal('1'), min_stock=0)
    db.session.add_all([cat, cafe, almendras_supply])
    db.session.flush()
    cortado = Product(name='Cortado', category_id=cat.id, has_recipe=True)
    medialuna = Product(name='Medialuna', category_id=cat.id, has_recipe=False, track_stock=True)
    group = ModifierGroup(name='Tipo de leche', min_select=1, max_select=1)
    extras = ModifierGroup(name='Extras', min_select=0, max_select=2)
    db.session.add_all([cortado, medialuna, group, extras])
    db.session.flush()
    taza = ProductVariant(product_id=cortado.id, name='Taza', price=Decimal('2000'), stock_quantity=0, min_stock=0)
    unidad = ProductVariant(product_id=medialuna.id, name='Unidad', price=Decimal('900'),
                            stock_quantity=Decimal('5'), min_stock=0)
    entera = ModifierOption(group_id=group.id, name='Entera', price_delta=0, position=0)
    almendras = ModifierOption(group_id=group.id, name='Almendras', price_delta=Decimal('300'),
                               supply_id=almendras_supply.id, supply_quantity=Decimal('0.2'), position=1)
    canela = ModifierOption(group_id=extras.id, name='Canela', price_delta=Decimal('100'), position=0)
    db.session.add_all([taza, unidad, entera, almendras, canela])
    db.session.add(ProductRecipeItem(product_id=cortado.id, supply_id=cafe.id, quantity=Decimal('0.02'), unit='kg'))
    db.session.add(ProductModifierGroup(product_id=cortado.id, group_id=group.id, position=0))
    db.session.add(ProductModifierGroup(product_id=cortado.id, group_id=extras.id, position=1))
    efectivo = PaymentMethod(name='Efectivo', kind='cash', position=0)
    debito = PaymentMethod(name='Débito', kind='card', position=1)
    empleado = DiscountTemplate(name='Empleado', kind='percent', value=Decimal('20'), scope='sale', restricted=True)
    cortesia = DiscountTemplate(name='Cortesía', kind='percent', value=Decimal('100'), scope='item', restricted=False)
    db.session.add_all([efectivo, debito, empleado, cortesia])
    db.session.commit()
    return SimpleNamespace(category=cat, cafe=cafe, almendras_supply=almendras_supply, cortado=cortado,
                           medialuna=medialuna, taza=taza, unidad=unidad, group=group, extras=extras,
                           entera=entera, almendras=almendras, canela=canela, efectivo=efectivo, debito=debito,
                           empleado=empleado, cortesia=cortesia)
```

- [ ] **Step 2: Test que falla** — `backend/tests/test_pos_open_items.py`:

```python
from decimal import Decimal

import pytest

from app.extensions import db
from app.models.pos import PosSaleEvent
from app.services.pos import sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def test_open_salon_sale_numbers_daily(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _salon, t1, t2 = make_floor()
    first = sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=2)
    second = sale_service.open_sale(waiter, 'salon', table_id=t2.id, people=1)
    assert (first.number, second.number) == (1, 2)
    assert first.status == 'open' and first.waiter_id == waiter.id
    assert PosSaleEvent.query.filter_by(sale_id=first.id, event_type='opened').count() == 1


def test_open_on_busy_table_is_409_with_existing_sale(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _salon, t1, _t2 = make_floor()
    sale = sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=2)
    with pytest.raises(PosError) as exc:
        sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=2)
    assert exc.value.status == 409 and exc.value.extra == {'sale_id': sale.id}


def test_salon_sale_requires_people(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _salon, t1, _t2 = make_floor()
    with pytest.raises(PosError) as exc:
        sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=0)
    assert exc.value.status == 400


def test_counter_sale_needs_pos_module(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cashier = make_user('caja@test.com', modules=('POS',))
    with pytest.raises(PosError) as exc:
        sale_service.open_sale(waiter, 'counter')
    assert exc.value.status == 403
    sale = sale_service.open_sale(cashier, 'counter', customer_name='Ana')
    assert sale.table_id is None and sale.customer_name == 'Ana'


def test_add_item_with_modifiers_and_note(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    sale = sale_service.open_sale(cashier, 'counter')
    sale = sale_service.add_item(cashier, sale.id, cat.taza.id, quantity=2,
                                 modifier_option_ids=[cat.almendras.id, cat.canela.id], note='bien caliente')
    item = sale.items[0]
    assert item.status == 'pending' and item.product_name == 'Cortado' and item.variant_name == 'Taza'
    assert item.modifiers_total == Decimal('400') and item.line_total == Decimal('4800')
    assert [m.option_name for m in item.modifiers] == ['Almendras', 'Canela']
    assert sale.subtotal == Decimal('4800') and sale.total == Decimal('4800')


@pytest.mark.parametrize('options, message', [
    ([], 'Elegí al menos 1 en "Tipo de leche"'),
    (['entera', 'almendras'], 'Podés elegir hasta 1 en "Tipo de leche"'),
])
def test_modifier_rules(pos_app, options, message):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    sale = sale_service.open_sale(cashier, 'counter')
    with pytest.raises(PosError) as exc:
        sale_service.add_item(cashier, sale.id, cat.taza.id, modifier_option_ids=[getattr(cat, o).id for o in options])
    assert exc.value.status == 400 and exc.value.message == message


def test_modifier_from_other_product_is_rejected(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    sale = sale_service.open_sale(cashier, 'counter')
    with pytest.raises(PosError) as exc:
        sale_service.add_item(cashier, sale.id, cat.unidad.id, modifier_option_ids=[cat.canela.id])
    assert 'no corresponde' in exc.value.message


def test_delete_pending_item_is_audited(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    sale = sale_service.open_sale(cashier, 'counter')
    sale = sale_service.add_item(cashier, sale.id, cat.unidad.id, quantity=3)
    item_id = sale.items[0].id
    sale = sale_service.delete_item(cashier, sale.id, item_id)
    assert sale.items == [] and sale.total == Decimal('0')
    event = PosSaleEvent.query.filter_by(event_type='item_deleted').one()
    assert event.item_id == item_id and event.payload['product'] == 'Medialuna' and event.payload['quantity'] == '3.000'


def test_inactive_variant_is_rejected(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    cat.unidad.is_active = False
    db.session.commit()
    sale = sale_service.open_sale(cashier, 'counter')
    with pytest.raises(PosError) as exc:
        sale_service.add_item(cashier, sale.id, cat.unidad.id)
    assert exc.value.status == 400
```

- [ ] **Step 3: Correr y ver que falla** (`ImportError: sale_service`).

- [ ] **Step 4: `errors.py`**

```python
class PosError(Exception):
    """Error de negocio del POS. Las rutas lo traducen a {'error': message, **extra} con `status`."""

    def __init__(self, message, status=409, **extra):
        super().__init__(message)
        self.message = message
        self.status = status
        self.extra = extra


def bad_request(message, **extra):
    return PosError(message, 400, **extra)


def forbidden(message):
    return PosError(message, 403)


def not_found(message):
    return PosError(message, 404)
```

- [ ] **Step 5: `audit.py`**

```python
from datetime import datetime
from decimal import Decimal

from app.extensions import db
from app.models.pos import PosSaleEvent


def _jsonable(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def record(sale, user, event_type, item=None, item_id=None, **payload):
    """Registra un evento de auditoría en la transacción actual."""
    db.session.add(PosSaleEvent(
        sale_id=sale.id,
        item_id=item.id if item is not None else item_id,
        user_id=user.id,
        event_type=event_type,
        payload=_jsonable(payload),
        created_at=datetime.utcnow(),
    ))
```

- [ ] **Step 6: `stock_hooks.py`**

```python
"""Stock de los ítems del POS: se descuenta al confirmar y se devuelve al anular."""
from collections import defaultdict
from decimal import Decimal

from app.services.stock_service import move_stock, stock_requirements


def _requirements(items):
    variants = defaultdict(Decimal)
    extra_supplies = defaultdict(Decimal)
    for item in items:
        quantity = Decimal(item.quantity)
        variants[item.product_variant_id] += quantity
        for modifier in item.modifiers:
            if modifier.supply_id and modifier.supply_quantity:
                extra_supplies[modifier.supply_id] += Decimal(modifier.supply_quantity) * quantity
    return stock_requirements(dict(variants), dict(extra_supplies))


def consume(items):
    """Descuenta el stock de ítems recién confirmados. Puede quedar negativo: la venta no se frena."""
    if items:
        variants, supplies = _requirements(items)
        move_stock(variants, supplies, sign=-1, allow_negative=True)


def restore(items):
    """Devuelve el stock de ítems confirmados que se anulan."""
    if items:
        variants, supplies = _requirements(items)
        move_stock(variants, supplies, sign=1)
```

- [ ] **Step 7: `common.py`**

```python
"""Utilidades compartidas por los servicios del POS."""
from datetime import datetime
from decimal import Decimal

from app.models.pos import PosSale
from app.services.pos import pricing
from app.services.pos.errors import PosError, bad_request, forbidden, not_found
from app.utils.permissions import check_module_access
from app.utils.validation import clean_str

MAX_QUANTITY = Decimal('1000')
MAX_MONEY = Decimal('10000000000')  # Numeric(12, 2)


def now():
    return datetime.utcnow()


def parse_id(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise bad_request(f'{label} es inválido')
    return value


def require_reason(reason):
    reason = clean_str(reason, 255)
    if not reason:
        raise bad_request('Indicá el motivo')
    return reason


def require_module(user, module, message):
    if not check_module_access(user, module):
        raise forbidden(message)


def require_status(sale, statuses, message):
    if sale.status not in statuses:
        raise PosError(message)


def load_sale(sale_id):
    """Trae la venta bloqueando su fila (SELECT ... FOR UPDATE) y con valores frescos."""
    sale = PosSale.query.filter_by(id=sale_id).with_for_update().populate_existing().first()
    if sale is None:
        raise not_found('La venta no existe')
    return sale


def active_payments(sale):
    return [p for p in sale.payments if p.cancelled_at is None]


def recalc(sale):
    """Recalcula montos de descuentos y totales de la venta a partir de sus filas."""
    from app.extensions import db
    db.session.flush()
    lines = [pricing.Line(i.id, i.line_total) for i in sale.items if i.status != 'cancelled']
    discounts = [d for d in sale.discounts if d.cancelled_at is None]
    totals = pricing.compute(lines, [pricing.Disc(d.id, d.item_id, d.kind, d.value) for d in discounts])
    for discount in discounts:
        discount.amount = totals.amounts[discount.id]
    sale.subtotal = totals.subtotal
    sale.discount_total = totals.discount_total
    sale.total = totals.total
    sale.paid_total = pricing.money(sum((p.amount for p in active_payments(sale)), Decimal('0')))


def display_name(user):
    if user is None:
        return None
    employee = getattr(user, 'employee', None)
    return employee.full_name if employee else user.email
```

- [ ] **Step 8: `serializers.py`**

```python
from app.services.pos.common import display_name


def _money(value):
    return float(value) if value is not None else None


def _iso(value):
    return value.isoformat() if value is not None else None


def item_to_dict(item):
    return {
        'id': item.id,
        'product_variant_id': item.product_variant_id,
        'product_name': item.product_name,
        'variant_name': item.variant_name,
        'unit_price': _money(item.unit_price),
        'quantity': float(item.quantity),
        'modifiers_total': _money(item.modifiers_total),
        'line_total': _money(item.line_total),
        'note': item.note,
        'status': item.status,
        'batch': item.batch,
        'created_at': _iso(item.created_at),
        'confirmed_at': _iso(item.confirmed_at),
        'cancelled_at': _iso(item.cancelled_at),
        'cancel_reason': item.cancel_reason,
        'modifiers': [{'option_id': m.option_id, 'group_name': m.group_name, 'option_name': m.option_name,
                       'price_delta': _money(m.price_delta)} for m in item.modifiers],
    }


def discount_to_dict(discount):
    return {
        'id': discount.id, 'item_id': discount.item_id, 'template_id': discount.template_id,
        'kind': discount.kind, 'value': _money(discount.value), 'amount': _money(discount.amount),
        'reason': discount.reason, 'is_active': discount.cancelled_at is None,
        'created_at': _iso(discount.created_at),
    }


def payment_to_dict(payment):
    return {
        'id': payment.id, 'payment_method_id': payment.payment_method_id, 'method_name': payment.method_name,
        'amount': _money(payment.amount), 'tendered': _money(payment.tendered), 'change': _money(payment.change),
        'is_active': payment.cancelled_at is None, 'cancel_reason': payment.cancel_reason,
        'created_at': _iso(payment.created_at),
    }


def sale_to_dict(sale, include_items=True):
    table = sale.table
    data = {
        'id': sale.id,
        'number': sale.number,
        'business_date': sale.business_date.isoformat(),
        'sale_type': sale.sale_type,
        'status': sale.status,
        'table': ({'id': table.id, 'number': table.number, 'label': table.label, 'salon_id': table.salon_id,
                   'salon_name': table.salon.name} if table else None),
        'people': sale.people,
        'customer_name': sale.customer_name,
        'comment': sale.comment,
        'waiter': {'id': sale.waiter.id, 'name': display_name(sale.waiter)} if sale.waiter else None,
        'opened_at': _iso(sale.opened_at),
        'billing_at': _iso(sale.billing_at),
        'closed_at': _iso(sale.closed_at),
        'cancelled_at': _iso(sale.cancelled_at),
        'cancel_reason': sale.cancel_reason,
        'subtotal': _money(sale.subtotal),
        'discount_total': _money(sale.discount_total),
        'total': _money(sale.total),
        'paid_total': _money(sale.paid_total),
        'balance': _money(sale.balance),
        'split_from_id': sale.split_from_id,
        'sale_id': sale.sale_id,
    }
    if include_items:
        data['items'] = [item_to_dict(i) for i in sale.items]
        data['discounts'] = [discount_to_dict(d) for d in sale.discounts]
        data['payments'] = [payment_to_dict(p) for p in sale.payments]
    return data
```

- [ ] **Step 9: `sale_service.py` (apertura e ítems)**

```python
"""Operaciones sobre ventas del POS.

Cada función pública es una transacción completa: valida, aplica, audita y hace commit. Si
algo falla levanta PosError (o ValueError por datos inválidos) antes del commit; la ruta
hace rollback.
"""
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models import ProductVariant, User
from app.models.pos import (ACTIVE_SALE_STATUSES, ModifierGroup, ModifierOption, PosSale, PosSaleItem,
                            PosSaleItemModifier, PosTable, ProductModifierGroup)
from app.services.pos import audit, pricing
from app.services.pos.common import (MAX_QUANTITY, load_sale, now, parse_id, recalc, require_module,
                                     require_status)
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.timezone_utils import get_current_date_argentina
from app.utils.validation import clean_str, parse_decimal


def assign_number(sale):
    """Asigna el siguiente número del día. Si otra venta toma el mismo número al mismo tiempo,
    el UNIQUE(business_date, number) hace fallar el commit y la ruta responde 409."""
    last = db.session.query(func.max(PosSale.number)).filter(PosSale.business_date == sale.business_date).scalar()
    sale.number = (last or 0) + 1
    db.session.add(sale)
    db.session.flush()


def open_sale(user, sale_type, table_id=None, people=None, customer_name=None, comment=None, waiter_id=None):
    if sale_type not in ('salon', 'counter'):
        raise bad_request('Tipo de venta inválido')
    customer_name = clean_str(customer_name, 100)
    comment = clean_str(comment, 500)
    table = None
    if sale_type == 'salon':
        table_id = parse_id(table_id, 'La mesa')
        table = PosTable.query.filter_by(id=table_id).with_for_update().first()
        if table is None or not table.is_active:
            raise not_found('La mesa no existe')
        if isinstance(people, bool) or not isinstance(people, int) or not 1 <= people <= 100:
            raise bad_request('Indicá la cantidad de personas')
        existing = PosSale.query.filter(PosSale.table_id == table.id,
                                        PosSale.status.in_(ACTIVE_SALE_STATUSES)).first()
        if existing is not None:
            raise PosError('La mesa ya tiene una venta abierta', 409, sale_id=existing.id)
    else:
        require_module(user, 'POS', 'Solo la caja puede abrir ventas de mostrador')
        people = None
    waiter = user.id
    if waiter_id is not None:
        require_module(user, 'POS', 'Solo la caja puede asignar el mozo')
        waiter_id = parse_id(waiter_id, 'El mozo')
        if db.session.get(User, waiter_id) is None:
            raise bad_request('El mozo no existe')
        waiter = waiter_id
    sale = PosSale(business_date=get_current_date_argentina(), sale_type=sale_type,
                   table_id=table.id if table else None, people=people, customer_name=customer_name,
                   comment=comment, waiter_id=waiter, status='open', opened_at=now(), opened_by=user.id)
    assign_number(sale)
    audit.record(sale, user, 'opened', sale_type=sale_type, table_id=sale.table_id, people=people)
    db.session.commit()
    return sale


def _validate_modifiers(product_id, option_ids):
    if option_ids is None:
        option_ids = []
    if not isinstance(option_ids, list) or any(isinstance(i, bool) or not isinstance(i, int) for i in option_ids):
        raise bad_request('Modificadores inválidos')
    if len(set(option_ids)) != len(option_ids):
        raise bad_request('Hay modificadores repetidos')
    assigned = [a.group_id for a in ProductModifierGroup.query.filter_by(product_id=product_id).all()]
    groups = (ModifierGroup.query.filter(ModifierGroup.id.in_(assigned), ModifierGroup.is_active.is_(True)).all()
              if assigned else [])
    group_ids = {g.id for g in groups}
    options = ModifierOption.query.filter(ModifierOption.id.in_(option_ids)).all() if option_ids else []
    if len(options) != len(option_ids):
        raise bad_request('Modificador inexistente')
    chosen = defaultdict(int)
    for option in options:
        if not option.is_active or option.group_id not in group_ids:
            raise bad_request(f'El modificador "{option.name}" no corresponde a este producto')
        chosen[option.group_id] += 1
    for group in groups:
        count = chosen.get(group.id, 0)
        if count < group.min_select:
            raise bad_request(f'Elegí al menos {group.min_select} en "{group.name}"')
        if count > group.max_select:
            raise bad_request(f'Podés elegir hasta {group.max_select} en "{group.name}"')
    order = {group_id: index for index, group_id in enumerate(assigned)}
    return sorted(options, key=lambda o: (order.get(o.group_id, 0), o.position, o.id))


def _parse_quantity(value):
    quantity = parse_decimal(value, 'La cantidad', minimum=Decimal('0.001'), maximum=MAX_QUANTITY)
    return quantity.quantize(Decimal('0.001'))


def add_item(user, sale_id, product_variant_id, quantity=1, modifier_option_ids=None, note=None):
    sale = load_sale(sale_id)
    require_status(sale, ('open',), 'Solo se agregan ítems a una venta abierta')
    variant_id = parse_id(product_variant_id, 'El producto')
    variant = db.session.get(ProductVariant, variant_id)
    if variant is None or not variant.is_active or not variant.product.is_active:
        raise bad_request('El producto no está disponible')
    quantity = _parse_quantity(quantity)
    note = clean_str(note, 255)
    options = _validate_modifiers(variant.product_id, modifier_option_ids)
    modifiers_total = sum((Decimal(o.price_delta) for o in options), Decimal('0'))
    item = PosSaleItem(product_variant_id=variant.id, product_name=variant.product.name, variant_name=variant.name,
                       unit_price=variant.price, quantity=quantity, modifiers_total=modifiers_total, note=note,
                       line_total=pricing.line_total(quantity, variant.price, modifiers_total), status='pending',
                       created_by=user.id, created_at=now())
    for option in options:
        item.modifiers.append(PosSaleItemModifier(
            option_id=option.id, group_name=option.group.name, option_name=option.name,
            price_delta=option.price_delta, supply_id=option.supply_id, supply_quantity=option.supply_quantity))
    sale.items.append(item)
    recalc(sale)
    audit.record(sale, user, 'item_added', item=item, product=item.product_name, variant=item.variant_name,
                 quantity=quantity, modifiers=[o.name for o in options], note=note)
    db.session.commit()
    return sale


def _find_item(sale, item_id):
    item_id = parse_id(item_id, 'El ítem')
    item = next((i for i in sale.items if i.id == item_id), None)
    if item is None:
        raise not_found('El ítem no existe en esta venta')
    return item


def delete_item(user, sale_id, item_id):
    sale = load_sale(sale_id)
    require_status(sale, ('open',), 'Solo se borran ítems de una venta abierta')
    item = _find_item(sale, item_id)
    if item.status != 'pending':
        raise PosError('El ítem ya fue confirmado; para quitarlo hay que anularlo')
    audit.record(sale, user, 'item_deleted', item_id=item.id, product=item.product_name, variant=item.variant_name,
                 quantity=item.quantity, modifiers=[m.option_name for m in item.modifiers], note=item.note)
    sale.items.remove(item)
    recalc(sale)
    db.session.commit()
    return sale
```

- [ ] **Step 10: Correr** `tests/test_pos_open_items.py`. Esperado: todos pasan.

- [ ] **Step 11: Commit**

```bash
git add backend/app/services/pos backend/tests/pos_helpers.py backend/tests/test_pos_open_items.py
git commit -m "feat(pos): open sales and manage pending items with modifiers"
```

---

### Task 8: Tandas, stock, pedir cuenta y reabrir

**Files:**
- Modify: `backend/app/services/pos/sale_service.py`
- Test: `backend/tests/test_pos_batches.py`

- [ ] **Step 1: Test que falla** — `backend/tests/test_pos_batches.py`:

```python
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import ProductVariant, Supply
from app.services.pos import sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _sale_with_items(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=2)
    sale_service.add_item(user, sale.id, cat.taza.id, quantity=2, modifier_option_ids=[cat.almendras.id])
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=3)
    return sale


def test_confirm_batch_numbers_and_consumes_stock(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    sale = _sale_with_items(waiter, cat, t1)
    sale = sale_service.confirm_batch(waiter, sale.id)
    assert {i.status for i in sale.items} == {'confirmed'} and {i.batch for i in sale.items} == {1}
    assert Decimal(db.session.get(Supply, cat.cafe.id).stock_quantity) == Decimal('0.96')
    assert Decimal(db.session.get(Supply, cat.almendras_supply.id).stock_quantity) == Decimal('0.6')
    assert Decimal(db.session.get(ProductVariant, cat.unidad.id).stock_quantity) == Decimal('2')

    sale_service.add_item(waiter, sale.id, cat.unidad.id, quantity=4)
    sale = sale_service.confirm_batch(waiter, sale.id)
    assert sale.items[-1].batch == 2
    assert Decimal(db.session.get(ProductVariant, cat.unidad.id).stock_quantity) == Decimal('-2')


def test_confirm_without_pending_is_409(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _salon, t1, _t2 = make_floor()
    sale = sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=1)
    with pytest.raises(PosError) as exc:
        sale_service.confirm_batch(waiter, sale.id)
    assert exc.value.status == 409


def test_request_bill_requires_no_pending_and_reopen(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    sale = _sale_with_items(waiter, cat, t1)
    with pytest.raises(PosError, match='pendientes'):
        sale_service.request_bill(waiter, sale.id)
    sale_service.confirm_batch(waiter, sale.id)
    sale = sale_service.request_bill(waiter, sale.id)
    assert sale.status == 'billing' and sale.billing_at is not None
    with pytest.raises(PosError):
        sale_service.add_item(waiter, sale.id, cat.unidad.id)
    sale = sale_service.reopen(waiter, sale.id)
    assert sale.status == 'open'


def test_request_bill_on_empty_sale_is_409(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _salon, t1, _t2 = make_floor()
    sale = sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=1)
    with pytest.raises(PosError, match='ítems'):
        sale_service.request_bill(waiter, sale.id)
```

- [ ] **Step 2: Correr y ver que falla** (`AttributeError: confirm_batch`).

- [ ] **Step 3: Implementar** — en `sale_service.py`, agregar `stock_hooks` al import de `app.services.pos` (`from app.services.pos import audit, pricing, stock_hooks`) y al final del archivo:

```python
def confirm_pending(sale, user):
    """Confirma los ítems pendientes como una tanda nueva y descuenta su stock. No hace commit."""
    pending = [i for i in sale.items if i.status == 'pending']
    if not pending:
        return []
    batch = max((i.batch or 0) for i in sale.items) + 1
    timestamp = now()
    for item in pending:
        item.status = 'confirmed'
        item.batch = batch
        item.confirmed_by = user.id
        item.confirmed_at = timestamp
    stock_hooks.consume(pending)
    audit.record(sale, user, 'batch_confirmed', batch=batch, item_ids=[i.id for i in pending])
    return pending


def confirm_batch(user, sale_id):
    sale = load_sale(sale_id)
    require_status(sale, ('open',), 'Solo se confirman pedidos de una venta abierta')
    if not confirm_pending(sale, user):
        raise PosError('No hay ítems nuevos para confirmar')
    db.session.commit()
    return sale


def request_bill(user, sale_id):
    sale = load_sale(sale_id)
    require_status(sale, ('open',), 'La venta no está abierta')
    if any(i.status == 'pending' for i in sale.items):
        raise PosError('Confirmá o borrá los ítems pendientes antes de pedir la cuenta')
    if not any(i.status == 'confirmed' for i in sale.items):
        raise PosError('La venta no tiene ítems confirmados')
    sale.status = 'billing'
    sale.billing_at = now()
    audit.record(sale, user, 'bill_requested', total=sale.total)
    db.session.commit()
    return sale


def reopen(user, sale_id):
    sale = load_sale(sale_id)
    require_status(sale, ('billing',), 'Solo se reabre una venta en cobro')
    sale.status = 'open'
    audit.record(sale, user, 'reopened')
    db.session.commit()
    return sale
```

- [ ] **Step 4: Correr** `tests/test_pos_batches.py tests/test_pos_open_items.py`. Esperado: todos pasan.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pos/sale_service.py backend/tests/test_pos_batches.py
git commit -m "feat(pos): confirm batches with stock consumption, request bill and reopen"
```

---

### Task 9: Descuentos

**Files:**
- Create: `backend/app/services/pos/discount_service.py`
- Test: `backend/tests/test_pos_discounts.py`

- [ ] **Step 1: Test que falla** — `backend/tests/test_pos_discounts.py`:

```python
from decimal import Decimal

import pytest

from app.services.pos import discount_service, sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _confirmed_sale(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=2)
    sale_service.add_item(user, sale.id, cat.taza.id, modifier_option_ids=[cat.entera.id])  # 2000
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=2)  # 1800
    return sale_service.confirm_batch(user, sale.id)


def test_unrestricted_item_template_for_waiter(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed_sale(waiter, cat, t1)
    sale = discount_service.add_discount(waiter, sale.id, item_id=sale.items[0].id, template_id=cat.cortesia.id)
    assert sale.discount_total == Decimal('2000') and sale.total == Decimal('1800')
    assert sale.discounts[0].reason == 'Cortesía'


def test_restricted_template_needs_permission(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    boss = make_user('jefe@test.com', modules=('Camarero', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed_sale(waiter, cat, t1)
    with pytest.raises(PosError) as exc:
        discount_service.add_discount(waiter, sale.id, template_id=cat.empleado.id)
    assert exc.value.status == 403
    sale = discount_service.add_discount(boss, sale.id, template_id=cat.empleado.id)
    assert sale.discount_total == Decimal('760') and sale.total == Decimal('3040')


def test_free_discount_needs_permission_and_reason(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    boss = make_user('jefe@test.com', modules=('Camarero', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed_sale(waiter, cat, t1)
    with pytest.raises(PosError) as exc:
        discount_service.add_discount(waiter, sale.id, kind='amount', value=100, reason='x')
    assert exc.value.status == 403
    with pytest.raises(PosError, match='motivo'):
        discount_service.add_discount(boss, sale.id, kind='amount', value=100)
    sale = discount_service.add_discount(boss, sale.id, kind='amount', value=5000, reason='Reclamo')
    assert sale.total == Decimal('0') and sale.discounts[0].amount == Decimal('3800')


def test_template_scope_must_match(pos_app):
    boss = make_user('jefe@test.com', modules=('Camarero', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed_sale(boss, cat, t1)
    with pytest.raises(PosError) as exc:
        discount_service.add_discount(boss, sale.id, template_id=cat.cortesia.id)
    assert exc.value.status == 400


def test_item_discount_only_on_confirmed_items(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=1)
    sale = sale_service.add_item(waiter, sale.id, cat.unidad.id)
    with pytest.raises(PosError) as exc:
        discount_service.add_discount(waiter, sale.id, item_id=sale.items[0].id, template_id=cat.cortesia.id)
    assert exc.value.status == 400


def test_cancel_discount_recalculates(pos_app):
    boss = make_user('jefe@test.com', modules=('Camarero', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed_sale(boss, cat, t1)
    sale = discount_service.add_discount(boss, sale.id, template_id=cat.empleado.id)
    sale = discount_service.cancel_discount(boss, sale.discounts[0].id)
    assert sale.discount_total == Decimal('0') and sale.total == Decimal('3800')
    assert sale.discounts[0].cancelled_at is not None
```

- [ ] **Step 2: Correr y ver que falla** (`ImportError: discount_service`).

- [ ] **Step 3: Implementar** — `backend/app/services/pos/discount_service.py`:

```python
"""Descuentos del POS: por venta o por ítem, libres o desde plantillas."""
from decimal import Decimal

from app.extensions import db
from app.models.pos import DiscountTemplate, PosDiscount
from app.models.pos import ACTIVE_SALE_STATUSES
from app.services.pos import audit
from app.services.pos.common import load_sale, now, parse_id, recalc, require_module, require_status
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.validation import clean_str, parse_decimal

MAX_PERCENT = Decimal('100')
MAX_AMOUNT = Decimal('100000000')  # Numeric(10, 2)


def add_discount(user, sale_id, item_id=None, template_id=None, kind=None, value=None, reason=None):
    sale = load_sale(sale_id)
    require_status(sale, ACTIVE_SALE_STATUSES, 'Solo se descuenta en una venta abierta o en cobro')
    item = None
    if item_id is not None:
        item_id = parse_id(item_id, 'El ítem')
        item = next((i for i in sale.items if i.id == item_id), None)
        if item is None or item.status != 'confirmed':
            raise bad_request('Solo se descuentan ítems confirmados de esta venta')
    reason = clean_str(reason, 255)
    template = None
    if template_id is not None:
        template = db.session.get(DiscountTemplate, parse_id(template_id, 'La plantilla'))
        if template is None or not template.is_active:
            raise bad_request('La plantilla no existe')
        if (template.scope == 'item') != (item is not None):
            raise bad_request('Esa plantilla se aplica a ítems' if template.scope == 'item'
                              else 'Esa plantilla se aplica a la venta')
        if template.restricted:
            require_module(user, 'Descuentos', 'No tenés permiso para usar esa plantilla')
        kind, value = template.kind, Decimal(template.value)
        reason = reason or template.name
    else:
        require_module(user, 'Descuentos', 'No tenés permiso para hacer descuentos libres')
        if kind not in ('percent', 'amount'):
            raise bad_request('Tipo de descuento inválido')
        value = parse_decimal(value, 'El descuento', minimum=Decimal('0.01'), maximum=MAX_AMOUNT)
        if kind == 'percent' and value > MAX_PERCENT:
            raise bad_request('El porcentaje no puede superar 100')
        if not reason:
            raise bad_request('Indicá el motivo del descuento')
    discount = PosDiscount(sale=sale, item=item, template_id=template.id if template else None, kind=kind,
                           value=value, amount=Decimal('0'), reason=reason, created_by=user.id, created_at=now())
    db.session.add(discount)  # SQLAlchemy 2.0: asignar la relación no lo agrega a la sesión
    recalc(sale)
    if sale.total < sale.paid_total:
        raise PosError('El total quedaría por debajo de lo ya pagado; anulá un pago primero')
    audit.record(sale, user, 'discount_added', item=item, discount_id=discount.id, kind=kind, value=value,
                 amount=discount.amount, reason=reason, template_id=discount.template_id)
    db.session.commit()
    return sale


def cancel_discount(user, discount_id):
    discount = db.session.get(PosDiscount, parse_id(discount_id, 'El descuento'))
    if discount is None:
        raise not_found('El descuento no existe')
    sale = load_sale(discount.sale_id)
    require_status(sale, ACTIVE_SALE_STATUSES, 'Solo se modifica una venta abierta o en cobro')
    if discount.cancelled_at is not None:
        raise PosError('El descuento ya está anulado')
    if discount.template is None or discount.template.restricted:
        require_module(user, 'Descuentos', 'No tenés permiso para quitar ese descuento')
    discount.cancelled_at = now()
    discount.cancelled_by = user.id
    recalc(sale)
    audit.record(sale, user, 'discount_cancelled', item_id=discount.item_id, discount_id=discount.id)
    db.session.commit()
    return sale
```

- [ ] **Step 4: Correr** `tests/test_pos_discounts.py`. Esperado: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pos/discount_service.py backend/tests/test_pos_discounts.py
git commit -m "feat(pos): add sale and item discounts with permission-aware templates"
```

---

### Task 10: Cobros, cierre y proyección a `sales`

**Files:**
- Create: `backend/app/services/pos/projection.py`, `backend/app/services/pos/payment_service.py`
- Test: `backend/tests/test_pos_payments.py`

- [ ] **Step 1: Test que falla** — `backend/tests/test_pos_payments.py`:

```python
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Sale
from app.services.pos import discount_service, payment_service, sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _billing_sale(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=3)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=4)  # 3600
    sale_service.confirm_batch(user, sale.id)
    return sale_service.request_bill(user, sale.id)


def test_partial_payments_then_close_and_project(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(cashier, cat, t1)
    sale = payment_service.add_payment(cashier, sale.id, cat.debito.id, 1600)
    assert sale.status == 'billing' and sale.paid_total == Decimal('1600')
    sale = payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 2000, tendered=5000)
    assert sale.status == 'closed' and sale.closed_by == cashier.id
    cash = sale.payments[1]
    assert cash.tendered == Decimal('5000') and cash.change == Decimal('3000')
    row = db.session.get(Sale, sale.sale_id)
    assert row.source == 'galia' and row.total == Decimal('3600') and row.medio_pago == 'Mixto'
    assert row.mesa == 'Mesa 1' and row.sala == 'Salón' and row.personas == 3 and row.estado == 'Cerrada'
    assert row.tipo_venta == 'Local' and row.id_origen == str(sale.id) and row.fecha == sale.closed_at.date()


def test_payment_cannot_exceed_balance(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(cashier, cat, t1)
    with pytest.raises(PosError) as exc:
        payment_service.add_payment(cashier, sale.id, cat.debito.id, 4000)
    assert exc.value.status == 400


def test_tendered_only_for_cash_and_not_less_than_amount(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(cashier, cat, t1)
    with pytest.raises(PosError):
        payment_service.add_payment(cashier, sale.id, cat.debito.id, 100, tendered=200)
    with pytest.raises((PosError, ValueError)):  # validación de datos: la ruta la traduce a 400
        payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 100, tendered=50)


def test_open_salon_sale_cannot_be_paid(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = sale_service.open_sale(cashier, 'salon', table_id=t1.id, people=1)
    sale_service.add_item(cashier, sale.id, cat.unidad.id)
    sale_service.confirm_batch(cashier, sale.id)
    with pytest.raises(PosError) as exc:
        payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 900)
    assert exc.value.status == 409


def test_counter_sale_pays_while_open_confirming_pending(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    sale = sale_service.open_sale(cashier, 'counter', customer_name='Ana')
    sale_service.add_item(cashier, sale.id, cat.unidad.id, quantity=2)
    sale = payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 1800)
    assert sale.status == 'closed' and sale.items[0].status == 'confirmed'
    row = db.session.get(Sale, sale.sale_id)
    assert row.tipo_venta == 'Mostrador' and row.cliente == 'Ana' and row.medio_pago == 'Efectivo'


def test_idempotent_payment(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(cashier, cat, t1)
    payment_service.add_payment(cashier, sale.id, cat.debito.id, 1000, client_request_id='abc-1')
    sale = payment_service.add_payment(cashier, sale.id, cat.debito.id, 1000, client_request_id='abc-1')
    assert len(sale.payments) == 1 and sale.paid_total == Decimal('1000')


def test_close_zero_total_sale(pos_app):
    boss = make_user('jefe@test.com', modules=('POS', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(boss, cat, t1)
    discount_service.add_discount(boss, sale.id, kind='percent', value=100, reason='Invita la casa')
    sale = payment_service.close_sale(boss, sale.id)
    assert sale.status == 'closed' and db.session.get(Sale, sale.sale_id).total == Decimal('0')


def test_close_with_balance_is_409(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(cashier, cat, t1)
    with pytest.raises(PosError) as exc:
        payment_service.close_sale(cashier, sale.id)
    assert exc.value.status == 409
```

- [ ] **Step 2: Correr y ver que falla** (`ImportError: payment_service`).

- [ ] **Step 3: `projection.py`**

```python
"""Copia de las ventas cerradas del POS en `sales`, la tabla que leen los reportes."""
from app.extensions import db
from app.models import Sale
from app.services.pos.common import active_payments, display_name


def project(sale):
    """Crea la fila de `sales` de una venta recién cerrada (mismo criterio de fechas que fudo_sync:
    timestamps en UTC y fecha = día de cierre)."""
    methods = sorted({p.method_name for p in active_payments(sale)})
    table = sale.table
    row = Sale(
        source='galia',
        external_id=None,
        fecha=sale.closed_at.date(),
        creacion=sale.opened_at,
        cerrada=sale.closed_at,
        caja=None,
        estado='Cerrada',
        cliente=sale.customer_name,
        mesa=table.label if table else None,
        sala=table.salon.name if table else None,
        personas=sale.people,
        camarero=display_name(sale.waiter),
        medio_pago=(methods[0] if len(methods) == 1 else 'Mixto') if methods else None,
        total=sale.total,
        fiscal=False,
        tipo_venta='Local' if sale.sale_type == 'salon' else 'Mostrador',
        comentario=sale.comment,
        origen='Galia POS',
        id_origen=str(sale.id),
    )
    db.session.add(row)
    db.session.flush()
    sale.sale_id = row.id


def unproject(sale):
    """Borra la fila proyectada (al reabrir o anular una venta cerrada)."""
    if sale.sale_id is not None:
        row = db.session.get(Sale, sale.sale_id)
        if row is not None:
            db.session.delete(row)
        sale.sale_id = None
```

Antes de escribirlo, confirmar los nombres de columnas de `Sale` (`grep -n "Column(" backend/app/models/sale.py`). Si alguna no coincide (por ejemplo `camarero` vs `camarero_nombre`), usar el nombre real del modelo en `main`.

- [ ] **Step 4: `payment_service.py`**

```python
"""Cobros y cierre de ventas del POS."""
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.pos import PaymentMethod, PosPayment
from app.services.pos import audit, pricing, projection
from app.services.pos.common import (MAX_MONEY, active_payments, load_sale, now, parse_id, recalc, require_reason)
from app.services.pos.errors import PosError, bad_request, not_found
from app.services.pos.sale_service import confirm_pending
from app.utils.validation import clean_str, parse_decimal


def _close(sale, user):
    sale.status = 'closed'
    sale.closed_at = now()
    sale.closed_by = user.id
    projection.project(sale)
    audit.record(sale, user, 'closed', total=sale.total, paid_total=sale.paid_total)


def _existing_payment(client_request_id, sale_id):
    payment = PosPayment.query.filter_by(client_request_id=client_request_id).first()
    if payment is not None and payment.sale_id != sale_id:
        raise PosError('Ese identificador de pago ya se usó en otra venta')
    return payment


def add_payment(user, sale_id, payment_method_id, amount, tendered=None, client_request_id=None):
    request_id = clean_str(client_request_id, 64)
    if request_id is not None and _existing_payment(request_id, sale_id) is not None:
        return load_sale(sale_id)
    sale = load_sale(sale_id)
    if sale.status == 'open' and sale.sale_type == 'counter':
        confirm_pending(sale, user)
        recalc(sale)
    elif sale.status != 'billing':
        raise PosError('Pedí la cuenta antes de cobrar')
    if not any(i.status == 'confirmed' for i in sale.items):
        raise PosError('La venta no tiene ítems para cobrar')
    method = db.session.get(PaymentMethod, parse_id(payment_method_id, 'El medio de pago'))
    if method is None or not method.is_active:
        raise bad_request('El medio de pago no existe')
    amount = pricing.money(parse_decimal(amount, 'El monto', minimum=Decimal('0.01'), maximum=MAX_MONEY))
    if amount > sale.balance:
        raise bad_request(f'El monto supera el saldo de {sale.balance}')
    change = None
    if tendered is not None:
        if method.kind != 'cash':
            raise bad_request('El vuelto solo aplica a pagos en efectivo')
        tendered = pricing.money(parse_decimal(tendered, 'El monto entregado', minimum=amount, maximum=MAX_MONEY))
        change = tendered - amount
    payment = PosPayment(payment_method_id=method.id, method_name=method.name, amount=amount, tendered=tendered,
                         change=change, client_request_id=request_id, created_by=user.id, created_at=now())
    sale.payments.append(payment)
    try:
        recalc(sale)
    except IntegrityError:
        db.session.rollback()
        if request_id is not None and _existing_payment(request_id, sale_id) is not None:
            return load_sale(sale_id)
        raise
    audit.record(sale, user, 'payment_added', payment_id=payment.id, method=method.name, amount=amount,
                 tendered=tendered, change=change)
    if sale.paid_total >= sale.total:
        _close(sale, user)
    db.session.commit()
    return sale


def close_sale(user, sale_id):
    """Cierra una venta sin saldo (por ejemplo, total 0 por descuentos)."""
    sale = load_sale(sale_id)
    if sale.status != 'billing':
        raise PosError('Pedí la cuenta antes de cerrar')
    if sale.balance > 0:
        raise PosError(f'La venta tiene saldo pendiente ({sale.balance})')
    _close(sale, user)
    db.session.commit()
    return sale


def cancel_payment(user, payment_id, reason):
    reason = require_reason(reason)
    payment = db.session.get(PosPayment, parse_id(payment_id, 'El pago'))
    if payment is None:
        raise not_found('El pago no existe')
    sale = load_sale(payment.sale_id)
    if payment.cancelled_at is not None:
        raise PosError('El pago ya está anulado')
    if sale.status not in ('billing', 'closed'):
        raise PosError('Solo se anulan pagos de una venta en cobro o cerrada')
    payment.cancelled_at = now()
    payment.cancelled_by = user.id
    payment.cancel_reason = reason
    if sale.status == 'closed':
        projection.unproject(sale)
        sale.status = 'billing'
        sale.closed_at = None
        sale.closed_by = None
    recalc(sale)
    audit.record(sale, user, 'payment_cancelled', payment_id=payment.id, amount=payment.amount, reason=reason)
    db.session.commit()
    return sale
```

- [ ] **Step 5: Correr** `tests/test_pos_payments.py`. Esperado: 8 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/pos/projection.py backend/app/services/pos/payment_service.py backend/tests/test_pos_payments.py
git commit -m "feat(pos): register payments, close sales and project them into sales"
```

---

### Task 11: Anulaciones (ítem, pago, venta)

**Files:**
- Modify: `backend/app/services/pos/sale_service.py`
- Test: `backend/tests/test_pos_cancellations.py`

- [ ] **Step 1: Test que falla** — `backend/tests/test_pos_cancellations.py`:

```python
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import ProductVariant, Sale
from app.models.pos import PosSaleEvent
from app.services.pos import discount_service, payment_service, sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _confirmed(user, cat, table, quantity=3):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=2)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=quantity)
    return sale_service.confirm_batch(user, sale.id)


def test_cancel_confirmed_item_restores_stock_and_discounts(pos_app):
    boss = make_user('jefe@test.com', modules=('POS', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed(boss, cat, t1)
    item_id = sale.items[0].id
    discount_service.add_discount(boss, sale.id, item_id=item_id, kind='amount', value=100, reason='x')
    sale = sale_service.cancel_item(boss, sale.id, item_id, 'El cliente cambió')
    item = sale.items[0]
    assert item.status == 'cancelled' and item.cancel_reason == 'El cliente cambió'
    assert sale.discounts[0].cancelled_at is not None and sale.total == Decimal('0')
    assert Decimal(db.session.get(ProductVariant, cat.unidad.id).stock_quantity) == Decimal('5')
    assert PosSaleEvent.query.filter_by(event_type='item_cancelled').one().payload['reason'] == 'El cliente cambió'


def test_cancel_item_requires_reason_and_confirmed_status(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = sale_service.open_sale(boss, 'salon', table_id=t1.id, people=1)
    sale = sale_service.add_item(boss, sale.id, cat.unidad.id)
    with pytest.raises(PosError, match='motivo'):
        sale_service.cancel_item(boss, sale.id, sale.items[0].id, '  ')
    with pytest.raises(PosError, match='pendiente'):
        sale_service.cancel_item(boss, sale.id, sale.items[0].id, 'x')


def test_cancel_item_below_paid_is_409(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed(boss, cat, t1, quantity=2)
    sale_service.request_bill(boss, sale.id)
    payment_service.add_payment(boss, sale.id, cat.debito.id, 1000)
    with pytest.raises(PosError) as exc:
        sale_service.cancel_item(boss, sale.id, sale.items[0].id, 'x')
    assert exc.value.status == 409


def test_cancel_payment_reopens_closed_sale_and_removes_projection(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed(boss, cat, t1, quantity=1)
    sale_service.request_bill(boss, sale.id)
    sale = payment_service.add_payment(boss, sale.id, cat.debito.id, 900)
    projected_id = sale.sale_id
    sale = payment_service.cancel_payment(boss, sale.payments[0].id, 'Se cobró mal')
    assert sale.status == 'billing' and sale.sale_id is None and sale.paid_total == Decimal('0')
    assert db.session.get(Sale, projected_id) is None


def test_cancel_sale_restores_stock_and_requires_no_payments(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed(boss, cat, t1, quantity=2)
    sale_service.request_bill(boss, sale.id)
    payment_service.add_payment(boss, sale.id, cat.debito.id, 100)
    with pytest.raises(PosError, match='pagos'):
        sale_service.cancel_sale(boss, sale.id, 'x')
    payment_service.cancel_payment(boss, sale.payments[0].id, 'x')
    sale = sale_service.cancel_sale(boss, sale.id, 'Se fueron')
    assert sale.status == 'cancelled' and sale.cancel_reason == 'Se fueron'
    assert {i.status for i in sale.items} == {'cancelled'}
    assert Decimal(db.session.get(ProductVariant, cat.unidad.id).stock_quantity) == Decimal('5')
```

- [ ] **Step 2: Correr y ver que falla** (`AttributeError: cancel_item`).

- [ ] **Step 3: Implementar** — en `sale_service.py`, ampliar el import de `common` con `active_payments, require_reason`, y agregar al final:

```python
def _cancel_item_row(item, user, reason):
    item.status = 'cancelled'
    item.cancelled_at = now()
    item.cancelled_by = user.id
    item.cancel_reason = reason
    for discount in item.discounts:
        if discount.cancelled_at is None:
            discount.cancelled_at = now()
            discount.cancelled_by = user.id


def cancel_item(user, sale_id, item_id, reason):
    reason = require_reason(reason)
    sale = load_sale(sale_id)
    require_status(sale, ACTIVE_SALE_STATUSES, 'Solo se anulan ítems de una venta abierta o en cobro')
    item = _find_item(sale, item_id)
    if item.status == 'pending':
        raise PosError('El ítem está pendiente: borralo en lugar de anularlo')
    if item.status == 'cancelled':
        raise PosError('El ítem ya está anulado')
    _cancel_item_row(item, user, reason)
    stock_hooks.restore([item])
    recalc(sale)
    if sale.total < sale.paid_total:
        raise PosError('El total quedaría por debajo de lo ya pagado; anulá un pago primero')
    audit.record(sale, user, 'item_cancelled', item=item, product=item.product_name, quantity=item.quantity,
                 reason=reason)
    db.session.commit()
    return sale


def cancel_sale_rows(sale, user, reason):
    """Anula una venta sin pagos activos: ítems, descuentos y stock. No hace commit."""
    confirmed = [i for i in sale.items if i.status == 'confirmed']
    for item in sale.items:
        if item.status != 'cancelled':
            _cancel_item_row(item, user, reason)
    for discount in sale.discounts:
        if discount.cancelled_at is None:
            discount.cancelled_at = now()
            discount.cancelled_by = user.id
    stock_hooks.restore(confirmed)
    sale.status = 'cancelled'
    sale.cancelled_at = now()
    sale.cancelled_by = user.id
    sale.cancel_reason = reason
    recalc(sale)


def cancel_sale(user, sale_id, reason):
    reason = require_reason(reason)
    sale = load_sale(sale_id)
    require_status(sale, ACTIVE_SALE_STATUSES, 'Solo se anula una venta abierta o en cobro')
    if active_payments(sale):
        raise PosError('La venta tiene pagos; anulalos antes de anular la venta')
    cancel_sale_rows(sale, user, reason)
    audit.record(sale, user, 'cancelled', reason=reason)
    db.session.commit()
    return sale
```

- [ ] **Step 4: Correr** `tests/test_pos_cancellations.py tests/test_pos_payments.py`. Esperado: todos pasan.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pos/sale_service.py backend/tests/test_pos_cancellations.py
git commit -m "feat(pos): cancel items, payments and sales with stock restore and audit"
```

---

### Task 12: Mover de mesa y dividir la cuenta

**Files:**
- Modify: `backend/app/services/pos/sale_service.py`
- Test: `backend/tests/test_pos_move_split.py`

- [ ] **Step 1: Test que falla** — `backend/tests/test_pos_move_split.py`:

```python
from decimal import Decimal

import pytest

from app.models.pos import PosSale
from app.services.pos import discount_service, payment_service, sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _sale(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=3)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=3)  # 2700
    sale_service.add_item(user, sale.id, cat.taza.id, modifier_option_ids=[cat.entera.id])  # 2000
    return sale_service.confirm_batch(user, sale.id)


def test_move_to_free_table(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, t2 = make_floor()
    sale = _sale(waiter, cat, t1)
    sale = sale_service.move_sale(waiter, sale.id, t2.id)
    assert sale.table_id == t2.id


def test_move_to_busy_table_is_409(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, t2 = make_floor()
    sale = _sale(waiter, cat, t1)
    sale_service.open_sale(waiter, 'salon', table_id=t2.id, people=1)
    with pytest.raises(PosError) as exc:
        sale_service.move_sale(waiter, sale.id, t2.id)
    assert exc.value.status == 409


def test_split_part_of_a_line_with_amount_discount(pos_app):
    boss = make_user('jefe@test.com', modules=('POS', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _sale(boss, cat, t1)
    medialunas = sale.items[0]
    discount_service.add_discount(boss, sale.id, item_id=medialunas.id, kind='amount', value=300, reason='x')
    new = sale_service.split_sale(boss, sale.id, [{'item_id': medialunas.id, 'quantity': 1}])
    origin = PosSale.query.get(sale.id)
    assert new.status == 'billing' and new.split_from_id == origin.id and new.table_id == t1.id
    assert new.items[0].quantity == Decimal('1') and new.items[0].line_total == Decimal('900')
    assert origin.items[0].quantity == Decimal('2') and origin.items[0].line_total == Decimal('1800')
    assert new.discount_total == Decimal('100') and new.total == Decimal('800')
    assert origin.discount_total == Decimal('200') and origin.total == Decimal('3600')


def test_split_whole_items_moves_them(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _sale(waiter, cat, t1)
    cortado_id = sale.items[1].id
    new = sale_service.split_sale(waiter, sale.id, [{'item_id': cortado_id, 'quantity': 1}])
    assert [i.id for i in new.items] == [cortado_id] and new.total == Decimal('2000')
    assert PosSale.query.get(sale.id).total == Decimal('2700')


def test_split_everything_cancels_origin(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _sale(waiter, cat, t1)
    lines = [{'item_id': i.id, 'quantity': float(i.quantity)} for i in sale.items]
    sale_service.split_sale(waiter, sale.id, lines)
    origin = PosSale.query.get(sale.id)
    assert origin.status == 'cancelled' and origin.cancel_reason == 'Dividida'


def test_split_with_payments_is_409(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _sale(boss, cat, t1)
    sale_service.request_bill(boss, sale.id)
    payment_service.add_payment(boss, sale.id, cat.debito.id, 100)
    with pytest.raises(PosError) as exc:
        sale_service.split_sale(boss, sale.id, [{'item_id': sale.items[0].id, 'quantity': 1}])
    assert exc.value.status == 409


def test_split_more_than_available_is_400(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _sale(waiter, cat, t1)
    with pytest.raises(PosError) as exc:
        sale_service.split_sale(waiter, sale.id, [{'item_id': sale.items[0].id, 'quantity': 4}])
    assert exc.value.status == 400
```

- [ ] **Step 2: Correr y ver que falla** (`AttributeError: move_sale`).

- [ ] **Step 3: Implementar** — en `sale_service.py` ampliar el import de modelos con `PosDiscount`, y agregar al final:

```python
def move_sale(user, sale_id, table_id):
    sale = load_sale(sale_id)
    require_status(sale, ACTIVE_SALE_STATUSES, 'Solo se mueve una venta abierta o en cobro')
    if sale.sale_type != 'salon':
        raise PosError('Las ventas de mostrador no tienen mesa')
    table_id = parse_id(table_id, 'La mesa')
    if table_id == sale.table_id:
        raise bad_request('La venta ya está en esa mesa')
    target = PosTable.query.filter_by(id=table_id).with_for_update().first()
    if target is None or not target.is_active:
        raise not_found('La mesa no existe')
    busy = PosSale.query.filter(PosSale.table_id == target.id, PosSale.status.in_(ACTIVE_SALE_STATUSES)).first()
    if busy is not None:
        raise PosError('La mesa de destino está ocupada', 409, sale_id=busy.id)
    previous = sale.table_id
    sale.table_id = target.id
    audit.record(sale, user, 'moved', from_table_id=previous, to_table_id=target.id)
    db.session.commit()
    return sale


def _split_line(item, quantity, target):
    """Pasa `quantity` unidades de `item` a un renglón nuevo en `target`, repartiendo descuentos."""
    original = Decimal(item.quantity)
    clone = PosSaleItem(product_variant_id=item.product_variant_id, product_name=item.product_name,
                        variant_name=item.variant_name, unit_price=item.unit_price, quantity=quantity,
                        modifiers_total=item.modifiers_total, note=item.note,
                        line_total=pricing.line_total(quantity, item.unit_price, item.modifiers_total),
                        status='confirmed', batch=item.batch, created_by=item.created_by,
                        created_at=item.created_at, confirmed_by=item.confirmed_by, confirmed_at=item.confirmed_at)
    for modifier in item.modifiers:
        clone.modifiers.append(PosSaleItemModifier(
            option_id=modifier.option_id, group_name=modifier.group_name, option_name=modifier.option_name,
            price_delta=modifier.price_delta, supply_id=modifier.supply_id,
            supply_quantity=modifier.supply_quantity))
    target.items.append(clone)
    item.quantity = original - quantity
    item.line_total = pricing.line_total(item.quantity, item.unit_price, item.modifiers_total)
    db.session.flush()
    for discount in list(item.discounts):
        if discount.cancelled_at is not None:
            continue
        if discount.kind == 'percent':
            part = Decimal(discount.value)
        else:
            part = pricing.split_value(discount.value, quantity, original)
            discount.value = Decimal(discount.value) - part
        if part > 0:
            # SQLAlchemy 2.0: asignar la relación no agrega el objeto a la sesión; hay que agregarlo.
            db.session.add(PosDiscount(sale=target, item=clone, template_id=discount.template_id,
                                       kind=discount.kind, value=part, amount=Decimal('0'), reason=discount.reason,
                                       created_by=discount.created_by, created_at=discount.created_at))
    return clone


def split_sale(user, sale_id, lines):
    sale = load_sale(sale_id)
    require_status(sale, ACTIVE_SALE_STATUSES, 'Solo se divide una venta abierta o en cobro')
    if active_payments(sale):
        raise PosError('La venta tiene pagos; anulalos antes de dividir')
    if not isinstance(lines, list) or not lines:
        raise bad_request('Elegí los ítems a separar')
    requested = defaultdict(Decimal)
    for line in lines:
        if not isinstance(line, dict):
            raise bad_request('Ítem inválido')
        requested[parse_id(line.get('item_id'), 'El ítem')] += _parse_quantity(line.get('quantity'))
    items = {i.id: i for i in sale.items}
    for item_id, quantity in requested.items():
        item = items.get(item_id)
        if item is None or item.status != 'confirmed':
            raise bad_request('Solo se separan ítems confirmados de esta venta')
        if quantity > Decimal(item.quantity):
            raise bad_request(f'No hay tantas unidades de {item.product_name}')
    new = PosSale(business_date=get_current_date_argentina(), sale_type=sale.sale_type, table_id=sale.table_id,
                  people=1 if sale.sale_type == 'salon' else None, customer_name=sale.customer_name,
                  waiter_id=sale.waiter_id, status='billing', opened_at=now(), opened_by=user.id,
                  billing_at=now(), split_from_id=sale.id)
    assign_number(new)
    moved = []
    for item_id, quantity in requested.items():
        item = items[item_id]
        if quantity == Decimal(item.quantity):
            item.sale = new
            for discount in list(item.discounts):
                discount.sale = new
            moved.append({'item_id': item.id, 'quantity': quantity})
        else:
            clone = _split_line(item, quantity, new)
            moved.append({'item_id': item.id, 'new_item_id': clone.id, 'quantity': quantity})
    recalc(sale)
    recalc(new)
    audit.record(sale, user, 'split_out', to_sale_id=new.id, items=moved)
    audit.record(new, user, 'split_in', from_sale_id=sale.id, items=moved)
    if not any(i.status != 'cancelled' for i in sale.items):
        cancel_sale_rows(sale, user, 'Dividida')
        audit.record(sale, user, 'cancelled', reason='Dividida')
    db.session.commit()
    return new
```

Nota: `cancel_sale_rows` devuelve stock de los ítems confirmados que **queden** en la venta; al dividir todo, la venta de origen ya no tiene ítems confirmados (se movieron), así que no se devuelve stock de más.

- [ ] **Step 4: Correr** `tests/test_pos_move_split.py tests/test_pos_cancellations.py`. Esperado: todos pasan.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pos/sale_service.py backend/tests/test_pos_move_split.py
git commit -m "feat(pos): move sales between tables and split bills by items"
```

---

### Task 13: API de configuración, plano y catálogo

**Files:**
- Create: `backend/app/routes/pos_config.py`, `backend/app/routes/pos_floor.py`
- Modify: `backend/app/__init__.py`
- Test: `backend/tests/test_pos_config_api.py`

- [ ] **Step 1: Test que falla** — `backend/tests/test_pos_config_api.py`:

```python
from app.services.pos import sale_service
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


def test_salon_and_table_crud(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    headers = auth_headers(client, cashier)
    salon = client.post('/api/v1/pos/config/salons', json={'name': 'Terraza'}, headers=headers)
    assert salon.status_code == 201, salon.get_json()
    salon_id = salon.get_json()['id']
    table = client.post('/api/v1/pos/config/tables', json={'salon_id': salon_id, 'number': 7, 'capacity': 4},
                        headers=headers)
    assert table.status_code == 201
    dup = client.post('/api/v1/pos/config/tables', json={'salon_id': salon_id, 'number': 7}, headers=headers)
    assert dup.status_code == 409
    moved = client.put(f"/api/v1/pos/config/tables/{table.get_json()['id']}", json={'pos_x': 30, 'pos_y': 40},
                       headers=headers)
    assert moved.get_json()['pos_x'] == 30


def test_cannot_deactivate_busy_table(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    _s, t1, _t = make_floor()
    sale_service.open_sale(cashier, 'salon', table_id=t1.id, people=1)
    response = client.put(f'/api/v1/pos/config/tables/{t1.id}', json={'is_active': False},
                          headers=auth_headers(client, cashier))
    assert response.status_code == 409


def test_modifier_group_crud_and_assignment(pos_app):
    client = pos_app.test_client()
    admin = make_user('admin@test.com', role='admin')
    cat = make_catalog()
    headers = auth_headers(client, admin)
    created = client.post('/api/v1/pos/config/modifier-groups', headers=headers, json={
        'name': 'Endulzante', 'min_select': 0, 'max_select': 1,
        'options': [{'name': 'Azúcar'}, {'name': 'Stevia', 'price_delta': 50}]})
    assert created.status_code == 201, created.get_json()
    group = created.get_json()
    assert [o['name'] for o in group['options']] == ['Azúcar', 'Stevia']
    bad = client.post('/api/v1/pos/config/modifier-groups', headers=headers,
                      json={'name': 'X', 'min_select': 2, 'max_select': 1, 'options': [{'name': 'a'}]})
    assert bad.status_code == 400
    assigned = client.put(f'/api/v1/pos/config/products/{cat.medialuna.id}/modifier-groups', headers=headers,
                          json={'group_ids': [group['id']]})
    assert assigned.status_code == 200 and assigned.get_json()['group_ids'] == [group['id']]


def test_payment_methods_and_templates_admin_only(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    admin = make_user('admin@test.com', role='admin')
    denied = client.post('/api/v1/pos/config/payment-methods', json={'name': 'Cheque', 'kind': 'other'},
                         headers=auth_headers(client, cashier))
    assert denied.status_code == 403
    ok = client.post('/api/v1/pos/config/discount-templates', headers=auth_headers(client, admin),
                     json={'name': 'Happy hour', 'kind': 'percent', 'value': 15, 'scope': 'sale'})
    assert ok.status_code == 201 and ok.get_json()['restricted'] is False


def test_floor_shows_active_sales(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    salon, t1, t2 = make_floor()
    sale = sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=2)
    data = client.get('/api/v1/pos/floor', headers=auth_headers(client, waiter)).get_json()
    assert data['salon_id'] == salon.id
    by_number = {t['number']: t for t in data['tables']}
    assert by_number[1]['sales'][0]['id'] == sale.id and by_number[2]['sales'] == []


def test_catalog_lists_variants_and_modifiers(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    make_catalog()
    data = client.get('/api/v1/pos/catalog', headers=auth_headers(client, waiter)).get_json()
    cortado = next(p for p in data['products'] if p['name'] == 'Cortado')
    assert cortado['variants'][0]['price'] == 2000.0
    assert [g['name'] for g in cortado['modifier_groups']] == ['Tipo de leche', 'Extras']
    lookups = client.get('/api/v1/pos/payment-methods', headers=auth_headers(client, waiter)).get_json()
    assert [m['name'] for m in lookups['payment_methods']] == ['Efectivo', 'Débito']


def test_floor_requires_pos_or_camarero(pos_app):
    client = pos_app.test_client()
    nobody = make_user('x@test.com')
    assert client.get('/api/v1/pos/floor', headers=auth_headers(client, nobody)).status_code == 403
```

- [ ] **Step 2: Correr y ver que falla** (404).

- [ ] **Step 3: `pos_floor.py`**

```python
"""Lecturas del POS: plano de mesas, catálogo y listas para la UI."""
from collections import defaultdict

from flask import Blueprint, jsonify, request

from app.models import Product, ProductCategory
from app.models.pos import (ACTIVE_SALE_STATUSES, DiscountTemplate, ModifierGroup, PaymentMethod, PosSale, PosTable,
                            ProductModifierGroup, Salon)
from app.services.pos.serializers import sale_to_dict
from app.utils.decorators import module_required
from app.utils.jwt_utils import token_required

bp = Blueprint('pos_floor', __name__, url_prefix='/api/v1/pos')


@bp.route('/floor', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def floor(current_user):
    salons = Salon.query.filter_by(is_active=True).order_by(Salon.position, Salon.id).all()
    salon_id = request.args.get('salon_id', type=int) or (salons[0].id if salons else None)
    tables = (PosTable.query.filter_by(salon_id=salon_id, is_active=True).order_by(PosTable.number).all()
              if salon_id else [])
    active = (PosSale.query.filter(PosSale.table_id.in_([t.id for t in tables]),
                                   PosSale.status.in_(ACTIVE_SALE_STATUSES)).order_by(PosSale.opened_at).all()
              if tables else [])
    by_table = defaultdict(list)
    for sale in active:
        by_table[sale.table_id].append(sale_to_dict(sale, include_items=False))
    return jsonify({
        'salons': [s.to_dict() for s in salons],
        'salon_id': salon_id,
        'tables': [{**t.to_dict(), 'sales': by_table.get(t.id, [])} for t in tables],
    }), 200


@bp.route('/catalog', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def catalog(current_user):
    groups = {g.id: g for g in ModifierGroup.query.filter_by(is_active=True).all()}
    assignments = defaultdict(list)
    for assignment in ProductModifierGroup.query.order_by(ProductModifierGroup.position).all():
        if assignment.group_id in groups:
            assignments[assignment.product_id].append(groups[assignment.group_id].to_dict())
    products = []
    for product in Product.query.filter_by(is_active=True).order_by(Product.name).all():
        variants = [{'id': v.id, 'name': v.name, 'price': float(v.price)}
                    for v in product.variants if v.is_active]
        if not variants:
            continue
        products.append({'id': product.id, 'name': product.name, 'category_id': product.category_id,
                         'image_url': product.image_url, 'variants': variants,
                         'modifier_groups': assignments.get(product.id, [])})
    categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all()
    return jsonify({'categories': [{'id': c.id, 'name': c.name, 'color': c.color} for c in categories],
                    'products': products}), 200


@bp.route('/payment-methods', methods=['GET'])
@token_required
@module_required('POS', 'Camarero', 'Cobrar')
def payment_methods(current_user):
    methods = PaymentMethod.query.filter_by(is_active=True).order_by(PaymentMethod.position, PaymentMethod.id).all()
    return jsonify({'payment_methods': [m.to_dict() for m in methods]}), 200


@bp.route('/discount-templates', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def discount_templates(current_user):
    templates = DiscountTemplate.query.filter_by(is_active=True).order_by(DiscountTemplate.name).all()
    return jsonify({'discount_templates': [t.to_dict() for t in templates]}), 200
```

`product.variants` es una relación `lazy='dynamic'` en el modelo actual: iterarla funciona (hace la query). Si en `main` no lo es, el código sigue funcionando.

- [ ] **Step 4: `pos_config.py`**

```python
"""Configuración del POS: salones, mesas, modificadores, medios de pago y plantillas."""
import logging
from decimal import Decimal

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Product, Supply
from app.models.pos import (ACTIVE_SALE_STATUSES, DISCOUNT_KINDS, DISCOUNT_SCOPES, PAYMENT_KINDS, DiscountTemplate,
                            ModifierGroup, ModifierOption, PaymentMethod, PosSale, PosTable, ProductModifierGroup,
                            Salon)
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.decorators import admin_required, module_required
from app.utils.jwt_utils import token_required
from app.utils.validation import clean_str, json_object, parse_decimal

logger = logging.getLogger(__name__)
bp = Blueprint('pos_config', __name__, url_prefix='/api/v1/pos/config')


def _run(action, status=200):
    try:
        result = action()
        db.session.commit()
    except PosError as exc:
        db.session.rollback()
        return jsonify({'error': exc.message, **exc.extra}), exc.status
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Ya existe un registro con esos datos'}), 409
    except Exception:
        db.session.rollback()
        logger.exception('Error inesperado en la configuración del POS')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return jsonify(result), status


def _body():
    data = json_object()
    if data is None:
        raise bad_request('El cuerpo tiene que ser un objeto JSON')
    return data


def _int(value, label, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise bad_request(f'{label} es inválido')
    return value


def _name(data, max_len):
    name = clean_str(data.get('name'), max_len)
    if not name:
        raise bad_request('El nombre es obligatorio')
    return name


def _has_active_sales(table_ids):
    return bool(table_ids) and PosSale.query.filter(PosSale.table_id.in_(table_ids),
                                                    PosSale.status.in_(ACTIVE_SALE_STATUSES)).first() is not None


# Salones y mesas

@bp.route('/salons', methods=['GET'])
@token_required
@module_required('POS')
def list_salons(current_user):
    return jsonify({'salons': [s.to_dict() for s in Salon.query.order_by(Salon.position, Salon.id).all()]}), 200


@bp.route('/salons', methods=['POST'])
@token_required
@module_required('POS')
def create_salon(current_user):
    def action():
        data = _body()
        salon = Salon(name=_name(data, 100), position=_int(data.get('position', 0), 'La posición'))
        db.session.add(salon)
        db.session.flush()
        return salon.to_dict()
    return _run(action, 201)


@bp.route('/salons/<int:salon_id>', methods=['PUT'])
@token_required
@module_required('POS')
def update_salon(current_user, salon_id):
    def action():
        salon = db.session.get(Salon, salon_id)
        if salon is None:
            raise not_found('El salón no existe')
        data = _body()
        if 'name' in data:
            salon.name = _name(data, 100)
        if 'position' in data:
            salon.position = _int(data['position'], 'La posición')
        if 'is_active' in data:
            if data['is_active'] is False and _has_active_sales([t.id for t in salon.tables]):
                raise PosError('El salón tiene mesas con ventas abiertas')
            salon.is_active = bool(data['is_active'])
        db.session.flush()
        return salon.to_dict()
    return _run(action)


@bp.route('/tables', methods=['GET'])
@token_required
@module_required('POS')
def list_tables(current_user):
    query = PosTable.query
    salon_id = request.args.get('salon_id', type=int)
    if salon_id:
        query = query.filter_by(salon_id=salon_id)
    return jsonify({'tables': [t.to_dict() for t in query.order_by(PosTable.salon_id, PosTable.number).all()]}), 200


_TABLE_FLOATS = ('pos_x', 'pos_y', 'width', 'height')


def _apply_table(table, data):
    if 'number' in data:
        table.number = _int(data['number'], 'El número', minimum=1)
    if 'name' in data:
        table.name = clean_str(data['name'], 50)
    if 'capacity' in data:
        table.capacity = None if data['capacity'] is None else _int(data['capacity'], 'La capacidad', minimum=1)
    for field in _TABLE_FLOATS:
        if field in data:
            setattr(table, field, float(parse_decimal(data[field], field, minimum=Decimal('0'),
                                                      maximum=Decimal('100000'))))


@bp.route('/tables', methods=['POST'])
@token_required
@module_required('POS')
def create_table(current_user):
    def action():
        data = _body()
        salon = db.session.get(Salon, _int(data.get('salon_id'), 'El salón', minimum=1))
        if salon is None:
            raise not_found('El salón no existe')
        if 'number' not in data:
            raise bad_request('El número es obligatorio')
        table = PosTable(salon_id=salon.id)
        _apply_table(table, data)
        db.session.add(table)
        db.session.flush()
        return table.to_dict()
    return _run(action, 201)


@bp.route('/tables/<int:table_id>', methods=['PUT'])
@token_required
@module_required('POS')
def update_table(current_user, table_id):
    def action():
        table = db.session.get(PosTable, table_id)
        if table is None:
            raise not_found('La mesa no existe')
        data = _body()
        _apply_table(table, data)
        if 'is_active' in data:
            if data['is_active'] is False and _has_active_sales([table.id]):
                raise PosError('La mesa tiene una venta abierta')
            table.is_active = bool(data['is_active'])
        db.session.flush()
        return table.to_dict()
    return _run(action)


# Modificadores

def _apply_options(group, options):
    if not isinstance(options, list) or not options:
        raise bad_request('El grupo necesita al menos una opción')
    existing = {o.id: o for o in group.options}
    kept = set()
    for position, data in enumerate(options):
        if not isinstance(data, dict):
            raise bad_request('Opción inválida')
        option = existing.get(data.get('id')) if data.get('id') is not None else None
        if data.get('id') is not None and option is None:
            raise bad_request('La opción no pertenece a este grupo')
        if option is None:
            option = ModifierOption(group=group)
        option.name = _name(data, 100)
        option.price_delta = parse_decimal(data.get('price_delta', 0), 'El recargo', maximum=Decimal('100000000'))
        option.position = position
        option.is_active = True
        supply_id = data.get('supply_id')
        if supply_id is None:
            option.supply_id = None
            option.supply_quantity = None
        else:
            supply = db.session.get(Supply, _int(supply_id, 'El insumo', minimum=1))
            if supply is None:
                raise bad_request('El insumo no existe')
            option.supply_id = supply.id
            option.supply_quantity = parse_decimal(data.get('supply_quantity'), 'La cantidad de insumo',
                                                   minimum=Decimal('0.0001'), maximum=Decimal('1000000'))
        if option.id is not None:
            kept.add(option.id)
    for option_id, option in existing.items():
        if option_id not in kept:
            option.is_active = False


def _apply_group(group, data, creating):
    if creating or 'name' in data:
        group.name = _name(data, 100)
    if creating or 'min_select' in data:
        group.min_select = _int(data.get('min_select', 0), 'El mínimo')
    if creating or 'max_select' in data:
        group.max_select = _int(data.get('max_select', 1), 'El máximo', minimum=1)
    if group.min_select > group.max_select:
        raise bad_request('El mínimo no puede superar al máximo')
    if 'is_active' in data:
        group.is_active = bool(data['is_active'])
    if creating or 'options' in data:
        _apply_options(group, data.get('options'))


@bp.route('/modifier-groups', methods=['GET'])
@token_required
@module_required('Products', 'POS')
def list_modifier_groups(current_user):
    groups = ModifierGroup.query.order_by(ModifierGroup.name).all()
    return jsonify({'modifier_groups': [g.to_dict(include_inactive=True) for g in groups]}), 200


@bp.route('/modifier-groups', methods=['POST'])
@token_required
@module_required('Products')
def create_modifier_group(current_user):
    def action():
        group = ModifierGroup()
        db.session.add(group)
        _apply_group(group, _body(), creating=True)
        db.session.flush()
        return group.to_dict()
    return _run(action, 201)


@bp.route('/modifier-groups/<int:group_id>', methods=['PUT'])
@token_required
@module_required('Products')
def update_modifier_group(current_user, group_id):
    def action():
        group = db.session.get(ModifierGroup, group_id)
        if group is None:
            raise not_found('El grupo no existe')
        _apply_group(group, _body(), creating=False)
        db.session.flush()
        return group.to_dict(include_inactive=True)
    return _run(action)


@bp.route('/products/<int:product_id>/modifier-groups', methods=['PUT'])
@token_required
@module_required('Products')
def assign_modifier_groups(current_user, product_id):
    def action():
        product = db.session.get(Product, product_id)
        if product is None:
            raise not_found('El producto no existe')
        group_ids = _body().get('group_ids')
        if not isinstance(group_ids, list) or len(set(group_ids)) != len(group_ids):
            raise bad_request('Lista de grupos inválida')
        for group_id in group_ids:
            if db.session.get(ModifierGroup, _int(group_id, 'El grupo', minimum=1)) is None:
                raise bad_request('El grupo no existe')
        ProductModifierGroup.query.filter_by(product_id=product.id).delete()
        for position, group_id in enumerate(group_ids):
            db.session.add(ProductModifierGroup(product_id=product.id, group_id=group_id, position=position))
        db.session.flush()
        return {'product_id': product.id, 'group_ids': group_ids}
    return _run(action)


# Medios de pago y plantillas (solo admin)

def _apply_payment_method(method, data, creating):
    if creating or 'name' in data:
        method.name = _name(data, 50)
    if creating or 'kind' in data:
        if data.get('kind') not in PAYMENT_KINDS:
            raise bad_request('Tipo de medio de pago inválido')
        method.kind = data['kind']
    if 'position' in data:
        method.position = _int(data['position'], 'La posición')
    if 'is_active' in data:
        method.is_active = bool(data['is_active'])


@bp.route('/payment-methods', methods=['GET'])
@token_required
@admin_required
def list_payment_methods(current_user):
    methods = PaymentMethod.query.order_by(PaymentMethod.position, PaymentMethod.id).all()
    return jsonify({'payment_methods': [m.to_dict() for m in methods]}), 200


@bp.route('/payment-methods', methods=['POST'])
@token_required
@admin_required
def create_payment_method(current_user):
    def action():
        method = PaymentMethod()
        _apply_payment_method(method, _body(), creating=True)
        db.session.add(method)
        db.session.flush()
        return method.to_dict()
    return _run(action, 201)


@bp.route('/payment-methods/<int:method_id>', methods=['PUT'])
@token_required
@admin_required
def update_payment_method(current_user, method_id):
    def action():
        method = db.session.get(PaymentMethod, method_id)
        if method is None:
            raise not_found('El medio de pago no existe')
        _apply_payment_method(method, _body(), creating=False)
        db.session.flush()
        return method.to_dict()
    return _run(action)


def _apply_template(template, data, creating):
    if creating or 'name' in data:
        template.name = _name(data, 100)
    if creating or 'kind' in data:
        if data.get('kind') not in DISCOUNT_KINDS:
            raise bad_request('Tipo de descuento inválido')
        template.kind = data['kind']
    if creating or 'scope' in data:
        if data.get('scope') not in DISCOUNT_SCOPES:
            raise bad_request('Alcance inválido')
        template.scope = data['scope']
    if creating or 'value' in data:
        template.value = parse_decimal(data.get('value'), 'El valor', minimum=Decimal('0.01'),
                                       maximum=Decimal('100000000'))
    if template.kind == 'percent' and Decimal(template.value) > 100:
        raise bad_request('El porcentaje no puede superar 100')
    if 'restricted' in data:
        template.restricted = bool(data['restricted'])
    elif creating:
        template.restricted = False
    if 'is_active' in data:
        template.is_active = bool(data['is_active'])


@bp.route('/discount-templates', methods=['GET'])
@token_required
@admin_required
def list_discount_templates(current_user):
    templates = DiscountTemplate.query.order_by(DiscountTemplate.name).all()
    return jsonify({'discount_templates': [t.to_dict() for t in templates]}), 200


@bp.route('/discount-templates', methods=['POST'])
@token_required
@admin_required
def create_discount_template(current_user):
    def action():
        template = DiscountTemplate()
        _apply_template(template, _body(), creating=True)
        db.session.add(template)
        db.session.flush()
        return template.to_dict()
    return _run(action, 201)


@bp.route('/discount-templates/<int:template_id>', methods=['PUT'])
@token_required
@admin_required
def update_discount_template(current_user, template_id):
    def action():
        template = db.session.get(DiscountTemplate, template_id)
        if template is None:
            raise not_found('La plantilla no existe')
        _apply_template(template, _body(), creating=False)
        db.session.flush()
        return template.to_dict()
    return _run(action)
```

- [ ] **Step 5: Registrar** — en `backend/app/__init__.py` agregar `pos_config, pos_floor` al import de rutas y registrar `pos_config.bp` y `pos_floor.bp` después de `config_routes.config_bp`.

- [ ] **Step 6: Correr** `tests/test_pos_config_api.py tests/test_route_access_coverage.py`. Esperado: todos pasan.

- [ ] **Step 7: Commit**

```bash
git add backend/app/routes/pos_config.py backend/app/routes/pos_floor.py backend/app/__init__.py backend/tests/test_pos_config_api.py
git commit -m "feat(pos): add configuration, floor and catalog endpoints"
```

---

### Task 14: API de ventas

**Files:**
- Create: `backend/app/routes/pos_sales.py`
- Modify: `backend/app/__init__.py`
- Test: `backend/tests/test_pos_sales_api.py`

- [ ] **Step 1: Test que falla** — `backend/tests/test_pos_sales_api.py`:

```python
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _open(client, headers, table_id, people=2):
    return client.post('/api/v1/pos/sales', headers=headers,
                       json={'sale_type': 'salon', 'table_id': table_id, 'people': people})


def test_full_salon_flow_over_api(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    w = auth_headers(client, waiter)
    c = auth_headers(client, cashier)
    sale = _open(client, w, t1.id).get_json()
    assert sale['status'] == 'open' and sale['table']['label'] == 'Mesa 1'
    sid = sale['id']
    added = client.post(f'/api/v1/pos/sales/{sid}/items', headers=w,
                        json={'product_variant_id': cat.taza.id, 'modifier_option_ids': [cat.almendras.id],
                              'note': 'sin azúcar'})
    assert added.status_code == 200 and added.get_json()['total'] == 2300.0
    assert client.post(f'/api/v1/pos/sales/{sid}/confirm', headers=w).status_code == 200
    assert client.post(f'/api/v1/pos/sales/{sid}/request-bill', headers=w).get_json()['status'] == 'billing'
    paid = client.post(f'/api/v1/pos/sales/{sid}/payments', headers=c,
                       json={'payment_method_id': cat.efectivo.id, 'amount': 2300, 'tendered': 3000})
    body = paid.get_json()
    assert paid.status_code == 200 and body['status'] == 'closed' and body['payments'][0]['change'] == 700.0
    events = client.get(f'/api/v1/pos/sales/{sid}/events', headers=c).get_json()['events']
    assert [e['event_type'] for e in events][:2] == ['opened', 'item_added']


def test_waiter_without_cobrar_cannot_pay(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    w = auth_headers(client, waiter)
    sid = _open(client, w, t1.id).get_json()['id']
    response = client.post(f'/api/v1/pos/sales/{sid}/payments', headers=w,
                           json={'payment_method_id': cat.efectivo.id, 'amount': 1})
    assert response.status_code == 403


def test_waiter_with_cobrar_can_pay(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero', 'Cobrar'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    w = auth_headers(client, waiter)
    sid = _open(client, w, t1.id).get_json()['id']
    client.post(f'/api/v1/pos/sales/{sid}/items', headers=w, json={'product_variant_id': cat.unidad.id})
    client.post(f'/api/v1/pos/sales/{sid}/confirm', headers=w)
    client.post(f'/api/v1/pos/sales/{sid}/request-bill', headers=w)
    response = client.post(f'/api/v1/pos/sales/{sid}/payments', headers=w,
                           json={'payment_method_id': cat.debito.id, 'amount': 900})
    assert response.status_code == 200 and response.get_json()['status'] == 'closed'


def test_errors_are_json_with_spanish_messages(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _s, t1, _t = make_floor()
    w = auth_headers(client, waiter)
    first = _open(client, w, t1.id).get_json()
    busy = _open(client, w, t1.id)
    assert busy.status_code == 409 and busy.get_json() == {'error': 'La mesa ya tiene una venta abierta',
                                                           'sale_id': first['id']}
    bad = client.post('/api/v1/pos/sales', headers=w, json=['no', 'es', 'objeto'])
    assert bad.status_code == 400
    missing = client.get('/api/v1/pos/sales/999', headers=w)
    assert missing.status_code == 404


def test_cancel_endpoints_require_anular(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _s, t1, _t = make_floor()
    w = auth_headers(client, waiter)
    sid = _open(client, w, t1.id).get_json()['id']
    assert client.post(f'/api/v1/pos/sales/{sid}/cancel', headers=w, json={'reason': 'x'}).status_code == 403


def test_list_open_sales(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _s, t1, t2 = make_floor()
    w = auth_headers(client, waiter)
    _open(client, w, t1.id)
    _open(client, w, t2.id)
    data = client.get('/api/v1/pos/sales', headers=w).get_json()
    assert len(data['sales']) == 2 and 'items' not in data['sales'][0]
```

- [ ] **Step 2: Correr y ver que falla** (404).

- [ ] **Step 3: `pos_sales.py`**

```python
"""API de ventas del POS. Las rutas solo validan permisos y traducen errores; la lógica está en los servicios."""
import logging

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.pos import SALE_STATUSES, SALE_TYPES, PosSale, PosSaleEvent
from app.services.pos import discount_service, payment_service, sale_service
from app.services.pos.errors import PosError, not_found
from app.services.pos.serializers import sale_to_dict
from app.utils.decorators import module_required
from app.utils.jwt_utils import token_required

logger = logging.getLogger(__name__)
bp = Blueprint('pos_sales', __name__, url_prefix='/api/v1/pos')


def _body():
    data = request.get_json(silent=True)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise PosError('El cuerpo tiene que ser un objeto JSON', 400)
    return data


def _respond(action):
    """Ejecuta una acción del servicio y devuelve la venta resultante o el error como JSON."""
    try:
        sale = action()
    except PosError as exc:
        db.session.rollback()
        return jsonify({'error': exc.message, **exc.extra}), exc.status
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Otra operación modificó la venta al mismo tiempo, probá de nuevo'}), 409
    except Exception:
        db.session.rollback()
        logger.exception('Error inesperado en el POS')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return jsonify(sale_to_dict(sale)), 200


@bp.route('/sales', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def list_sales(current_user):
    statuses = [s for s in request.args.get('status', 'open,billing').split(',') if s in SALE_STATUSES]
    query = PosSale.query.filter(PosSale.status.in_(statuses))
    sale_type = request.args.get('type')
    if sale_type in SALE_TYPES:
        query = query.filter_by(sale_type=sale_type)
    sales = query.order_by(PosSale.opened_at.desc()).limit(200).all()
    return jsonify({'sales': [sale_to_dict(s, include_items=False) for s in sales]}), 200


@bp.route('/sales', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def open_sale(current_user):
    def action():
        data = _body()
        return sale_service.open_sale(current_user, data.get('sale_type'), table_id=data.get('table_id'),
                                      people=data.get('people'), customer_name=data.get('customer_name'),
                                      comment=data.get('comment'), waiter_id=data.get('waiter_id'))
    return _respond(action)


@bp.route('/sales/<int:sale_id>', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def get_sale(current_user, sale_id):
    def action():
        sale = db.session.get(PosSale, sale_id)
        if sale is None:
            raise not_found('La venta no existe')
        return sale
    return _respond(action)


@bp.route('/sales/<int:sale_id>/items', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def add_item(current_user, sale_id):
    def action():
        data = _body()
        return sale_service.add_item(current_user, sale_id, data.get('product_variant_id'),
                                     quantity=data.get('quantity', 1),
                                     modifier_option_ids=data.get('modifier_option_ids', []),
                                     note=data.get('note'))
    return _respond(action)


@bp.route('/sales/<int:sale_id>/items/<int:item_id>', methods=['DELETE'])
@token_required
@module_required('POS', 'Camarero')
def delete_item(current_user, sale_id, item_id):
    return _respond(lambda: sale_service.delete_item(current_user, sale_id, item_id))


@bp.route('/sales/<int:sale_id>/confirm', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def confirm(current_user, sale_id):
    return _respond(lambda: sale_service.confirm_batch(current_user, sale_id))


@bp.route('/sales/<int:sale_id>/items/<int:item_id>/cancel', methods=['POST'])
@token_required
@module_required('Anular')
def cancel_item(current_user, sale_id, item_id):
    return _respond(lambda: sale_service.cancel_item(current_user, sale_id, item_id, _body().get('reason')))


@bp.route('/sales/<int:sale_id>/request-bill', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def request_bill(current_user, sale_id):
    return _respond(lambda: sale_service.request_bill(current_user, sale_id))


@bp.route('/sales/<int:sale_id>/reopen', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def reopen(current_user, sale_id):
    return _respond(lambda: sale_service.reopen(current_user, sale_id))


@bp.route('/sales/<int:sale_id>/discounts', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def add_discount(current_user, sale_id):
    def action():
        data = _body()
        return discount_service.add_discount(current_user, sale_id, item_id=data.get('item_id'),
                                             template_id=data.get('template_id'), kind=data.get('kind'),
                                             value=data.get('value'), reason=data.get('reason'))
    return _respond(action)


@bp.route('/discounts/<int:discount_id>/cancel', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def cancel_discount(current_user, discount_id):
    return _respond(lambda: discount_service.cancel_discount(current_user, discount_id))


@bp.route('/sales/<int:sale_id>/payments', methods=['POST'])
@token_required
@module_required('POS', 'Cobrar')
def add_payment(current_user, sale_id):
    def action():
        data = _body()
        return payment_service.add_payment(current_user, sale_id, data.get('payment_method_id'), data.get('amount'),
                                           tendered=data.get('tendered'),
                                           client_request_id=data.get('client_request_id'))
    return _respond(action)


@bp.route('/payments/<int:payment_id>/cancel', methods=['POST'])
@token_required
@module_required('Anular')
def cancel_payment(current_user, payment_id):
    return _respond(lambda: payment_service.cancel_payment(current_user, payment_id, _body().get('reason')))


@bp.route('/sales/<int:sale_id>/close', methods=['POST'])
@token_required
@module_required('POS', 'Cobrar')
def close_sale(current_user, sale_id):
    return _respond(lambda: payment_service.close_sale(current_user, sale_id))


@bp.route('/sales/<int:sale_id>/move', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def move_sale(current_user, sale_id):
    return _respond(lambda: sale_service.move_sale(current_user, sale_id, _body().get('table_id')))


@bp.route('/sales/<int:sale_id>/split', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def split_sale(current_user, sale_id):
    """Devuelve la venta nueva; la UI recarga la original."""
    return _respond(lambda: sale_service.split_sale(current_user, sale_id, _body().get('items')))


@bp.route('/sales/<int:sale_id>/cancel', methods=['POST'])
@token_required
@module_required('Anular')
def cancel_sale(current_user, sale_id):
    return _respond(lambda: sale_service.cancel_sale(current_user, sale_id, _body().get('reason')))


@bp.route('/sales/<int:sale_id>/events', methods=['GET'])
@token_required
@module_required('POS')
def sale_events(current_user, sale_id):
    if db.session.get(PosSale, sale_id) is None:
        return jsonify({'error': 'La venta no existe'}), 404
    events = PosSaleEvent.query.filter_by(sale_id=sale_id).order_by(PosSaleEvent.id).all()
    return jsonify({'events': [e.to_dict() for e in events]}), 200
```

- [ ] **Step 4: Registrar** `pos_sales` en `backend/app/__init__.py` (import y `app.register_blueprint(pos_sales.bp)`).

- [ ] **Step 5: Correr** `tests/test_pos_sales_api.py tests/test_route_access_coverage.py`. Esperado: todos pasan.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routes/pos_sales.py backend/app/__init__.py backend/tests/test_pos_sales_api.py
git commit -m "feat(pos): add sales API with permission checks and JSON errors"
```

---

### Task 15: Tests de concurrencia en PostgreSQL

**Files:**
- Test: `backend/tests/test_pos_concurrency_pg.py`

Estos tests solo corren con la variable `POS_PG_TEST_URL` apuntando a una base PostgreSQL **descartable** (la borran y la recrean). Sin la variable se saltean.

- [ ] **Step 1: Escribir los tests** — `backend/tests/test_pos_concurrency_pg.py`:

```python
import os
import threading

import pytest

from app import create_app
from app.config import Config, config
from app.extensions import db
from app.models import User
from app.services.pos import payment_service, sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user

PG_URL = os.getenv('POS_PG_TEST_URL')
pytestmark = pytest.mark.skipif(not PG_URL, reason='POS_PG_TEST_URL no configurada')


class PgTestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = PG_URL


@pytest.fixture
def pg_app():
    config['pos_pg_test'] = PgTestConfig
    app = create_app('pos_pg_test')
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def _parallel(app, fn, workers=2):
    barrier = threading.Barrier(workers)
    results = [None] * workers

    def run(index):
        with app.app_context():
            barrier.wait()
            try:
                results[index] = ('ok', fn())
            except Exception as exc:  # noqa: BLE001 - el test inspecciona el error
                db.session.rollback()
                results[index] = ('error', exc)
            finally:
                db.session.remove()

    threads = [threading.Thread(target=run, args=(i,)) for i in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def test_two_waiters_opening_the_same_table(pg_app):
    with pg_app.app_context():
        user_id = make_user('mozo@test.com', modules=('Camarero',)).id
        table_id = make_floor()[1].id

    def open_table():
        user = db.session.get(User, user_id)
        return sale_service.open_sale(user, 'salon', table_id=table_id, people=2).id

    results = _parallel(pg_app, open_table)
    errors = [r[1] for r in results if r[0] == 'error']
    assert [r[0] for r in results].count('ok') == 1
    assert len(errors) == 1 and isinstance(errors[0], PosError) and errors[0].status == 409


def test_concurrent_payments_do_not_exceed_balance(pg_app):
    with pg_app.app_context():
        user = make_user('caja@test.com', modules=('POS',))
        cat = make_catalog()
        table = make_floor()[1]
        sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=1)
        sale_service.add_item(user, sale.id, cat.unidad.id, quantity=2)  # 1800
        sale_service.confirm_batch(user, sale.id)
        sale_service.request_bill(user, sale.id)
        ids = (user.id, sale.id, cat.debito.id)

    def pay():
        user = db.session.get(User, ids[0])
        return payment_service.add_payment(user, ids[1], ids[2], 1500).paid_total

    results = _parallel(pg_app, pay)
    assert [r[0] for r in results].count('ok') == 1
    error = next(r[1] for r in results if r[0] == 'error')
    assert isinstance(error, PosError) and error.status == 400
```

- [ ] **Step 2: Correr sin la variable** — `tests/test_pos_concurrency_pg.py`. Esperado: `2 skipped`.

- [ ] **Step 3: Correr contra PostgreSQL descartable** (Docker Desktop prendido):

```bash
docker run -d --name galia-pos-pg-test -e POSTGRES_USER=galia -e POSTGRES_PASSWORD=galia -e POSTGRES_DB=pos_test -p 55433:5432 postgres:15
```

Esperar unos segundos y correr con `POS_PG_TEST_URL=postgresql://galia:galia@localhost:55433/pos_test` en el entorno (PowerShell: `$env:POS_PG_TEST_URL='postgresql://galia:galia@localhost:55433/pos_test'`). Esperado: `2 passed`. Después: `docker rm -f galia-pos-pg-test`.

Si Docker no está disponible, reportarlo; la Task 16 lo vuelve a intentar.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_pos_concurrency_pg.py
git commit -m "test(pos): add PostgreSQL concurrency tests for tables and payments"
```

---

### Task 16: Verificación completa

**Files:** ninguno nuevo (solo correcciones si aparecen).

- [ ] **Step 1: Suite completa contra la línea base** (cwd `backend/`):

```
PY -m pytest -q -p no:cacheprovider -rfE > <scratch>/pos_sales_pytest.txt
PY scripts/compare_baseline.py <scratch>/pos_sales_pytest.txt ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt
```

Esperado: `Sin fallas nuevas.`

- [ ] **Step 2: Migraciones en PostgreSQL descartable** — con Docker:

```bash
docker run -d --name galia-pos-mig -e POSTGRES_USER=galia -e POSTGRES_PASSWORD=galia -e POSTGRES_DB=galia_pos -p 55432:5432 postgres:15
```

Con `FLASK_APP=run.py`, `FLASK_ENV=production` y `DATABASE_URL=postgresql://galia:galia@localhost:55432/galia_pos`:
- `flask db upgrade` → termina en `b1a4_add_pos_sales_engine (head)`.
- `flask db downgrade b1a3_add_site_config` → sin errores; `modules` vuelve a tener solo los módulos de antes.
- `flask db upgrade` de nuevo → sin errores.
- Verificar el seed: `docker exec galia-pos-mig psql -U galia -d galia_pos -c "SELECT name FROM modules WHERE name IN ('POS','Camarero','Cobrar','Anular','Descuentos');" -c "SELECT name, kind FROM payment_methods ORDER BY position;"` → 5 módulos y 5 medios de pago.
- `docker rm -f galia-pos-mig`.

- [ ] **Step 3: Tests de concurrencia** — repetir la Task 15, Step 3, si no se pudo correr antes.

- [ ] **Step 4: Prueba de humo por API** — con la base de la Task 16, Step 2 (antes de borrarla) y el backend levantado contra ella:
  - como admin: crear un salón y dos mesas, abrir una venta en la mesa 1, agregar un ítem, confirmar, pedir la cuenta, cobrar en efectivo con vuelto;
  - comprobar en `sales` la fila con `source='galia'`;
  - comprobar en `GET /api/v1/pos/sales/<id>/events` la secuencia de eventos.
  Las ventas de prueba quedan en la base descartable, que se borra al final.

- [ ] **Step 5: Commit de correcciones** (solo si hubo):

```bash
git add <archivos>
git commit -m "fix(pos): address issues found during sales engine verification"
```
