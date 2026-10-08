# Carta Digital Interactiva — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar la carta en PDF por una carta web interactiva (QR) administrada desde galia-app, con precios sincronizados desde Fudo y publicada como snapshot estático en S3.

**Architecture:** galia-app guarda categorías/ítems/variantes/tags en Postgres y cachea los productos de Fudo. "Publicar" genera `menu.json` y lo sube bajo el prefijo público `menu/` del bucket S3 existente. Un sitio estático nuevo (`menu-site/`) solo lee ese JSON. Una tarea nocturna sincroniza Fudo y republica si cambiaron precios y no había borradores.

**Tech Stack:** Flask + SQLAlchemy + Alembic + pytest + boto3 + Pillow (backend); React 18 + Vite + Tailwind + axios (admin `frontend/`); React 18 + Vite + Tailwind + Vitest (`menu-site/`); Render (static site + cron job).

**Spec:** `docs/superpowers/specs/2026-10-07-carta-digital-design.md`

**Branch:** `feature/carta-digital`

---

## File map

**Backend (crear)**
- `backend/app/utils/slug.py` — `slugify`, `unique_slug`
- `backend/app/utils/menu_storage.py` — `MenuStorage` (S3 restringido a `menu/`), `public_url`, `get_menu_storage`
- `backend/app/models/menu.py` — `MenuCategory`, `MenuItem`, `MenuItemVariant`, `MenuTag`, `menu_item_tags`, `FudoProduct`, `MenuSetting`
- `backend/migrations/versions/add_menu_tables.py`
- `backend/app/services/menu_sync_service.py` — sync Fudo, sin asignar, alertas
- `backend/app/services/menu_publish_service.py` — snapshot, hash, publicar, limpiar imágenes huérfanas
- `backend/app/services/menu_image_service.py` — validar/redimensionar/WebP
- `backend/app/routes/menu.py` — blueprint `/api/v1/menu`
- `backend/app/tasks/menu_tasks.py` — sync nocturno
- `backend/seed_menu.py` + `backend/data/menu_seed.json` — carga inicial
- `backend/tests/menu_fakes.py`, `backend/tests/conftest.py`
- `backend/tests/test_menu_slug.py`, `test_menu_storage.py`, `test_menu_models.py`, `test_fudo_client_products.py`, `test_menu_sync.py`, `test_menu_publish.py`, `test_menu_image.py`, `test_menu_routes.py`, `test_menu_routes_ops.py`, `test_menu_tasks.py`

**Backend (modificar)**
- `backend/requirements.txt` — `Pillow`
- `backend/app/models/__init__.py` — exportar modelos de carta
- `backend/app/__init__.py` — registrar blueprint `menu`
- `backend/app/utils/fudo_client.py` — productos y categorías de productos

**Admin (crear)**
- `frontend/src/services/menuService.js`
- `frontend/src/utils/menuFormat.js`
- `frontend/src/components/menu/ModalShell.jsx`
- `frontend/src/components/menu/CategoryCard.jsx`
- `frontend/src/components/menu/CategoryFormModal.jsx`
- `frontend/src/components/menu/FudoProductPicker.jsx`
- `frontend/src/components/menu/MenuItemModal.jsx`
- `frontend/src/components/menu/MenuSettingsPanel.jsx`
- `frontend/src/pages/Menu.jsx`
- `frontend/src/pages/MenuInbox.jsx`

**Admin (modificar)**
- `frontend/src/App.jsx` — rutas `/menu`, `/menu/inbox`
- `frontend/src/components/layout/Sidebar.jsx` — grupo "Carta"

**Carta pública (crear)** — `menu-site/` completo (ver Tasks 16–20)

**Infra (modificar)** — `render.yaml`

---

## Phase A — Backend

### Task 1: Dependencias y utilidad de slugs

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/utils/slug.py`
- Test: `backend/tests/test_menu_slug.py`

- [ ] **Step 1: Agregar Pillow**

Agregar al final de `backend/requirements.txt`:

```
Pillow==10.4.0
```

Run: `cd backend && pip install Pillow==10.4.0`
Expected: `Successfully installed Pillow-10.4.0` (o "Requirement already satisfied").

- [ ] **Step 2: Write the failing test**

`backend/tests/test_menu_slug.py`:

```python
from app.utils.slug import slugify


def test_slugify_removes_accents_and_symbols():
    assert slugify('Cafés Fríos & Frappé') == 'cafes-frios-frappe'


def test_slugify_collapses_separators():
    assert slugify('  Tortas   --  Postres ') == 'tortas-postres'


def test_slugify_empty_falls_back():
    assert slugify('¡¡!!') == 'item'
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && pytest tests/test_menu_slug.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.utils.slug'`

- [ ] **Step 4: Write implementation**

`backend/app/utils/slug.py`:

```python
import re
import unicodedata


def slugify(text):
    normalized = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower()).strip('-')
    return slug or 'item'


def unique_slug(model, text, exclude_id=None):
    """Devuelve un slug único para `model` (debe tener columnas `slug` e `id`)."""
    base = slugify(text)
    slug = base
    suffix = 2
    while True:
        query = model.query.filter_by(slug=slug)
        if exclude_id is not None:
            query = query.filter(model.id != exclude_id)
        if query.first() is None:
            return slug
        slug = f'{base}-{suffix}'
        suffix += 1
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_menu_slug.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/app/utils/slug.py backend/tests/test_menu_slug.py
git commit -m "feat(menu): add Pillow dependency and slug utility"
```

---

### Task 2: Almacenamiento S3 restringido a `menu/`

**Files:**
- Create: `backend/app/utils/menu_storage.py`
- Test: `backend/tests/test_menu_storage.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_menu_storage.py`:

```python
import pytest
from app.utils.menu_storage import MenuStorage, public_url


class FakeS3Client:
    def __init__(self, keys=None):
        self.calls = []
        self.keys = keys or []

    def put_object(self, **kwargs):
        self.calls.append(('put', kwargs))

    def delete_object(self, **kwargs):
        self.calls.append(('delete', kwargs))

    def get_paginator(self, name):
        assert name == 'list_objects_v2'
        keys = self.keys

        class Paginator:
            def paginate(self, Bucket, Prefix):
                yield {'Contents': [{'Key': k} for k in keys if k.startswith(Prefix)]}

        return Paginator()


def test_put_prefixes_key_with_menu():
    client = FakeS3Client()
    storage = MenuStorage(client=client, bucket='bucket')
    storage.put('menu.json', b'{}', 'application/json', 'public, max-age=60')
    op, kwargs = client.calls[0]
    assert op == 'put'
    assert kwargs == {
        'Bucket': 'bucket', 'Key': 'menu/menu.json', 'Body': b'{}',
        'ContentType': 'application/json', 'CacheControl': 'public, max-age=60',
    }


@pytest.mark.parametrize('bad_key', ['', '../secret.pdf', 'images/../../x', '/'])
def test_rejects_keys_outside_prefix(bad_key):
    storage = MenuStorage(client=FakeS3Client(), bucket='bucket')
    with pytest.raises(ValueError):
        storage.put(bad_key, b'x', 'text/plain', 'no-cache')


def test_delete_prefixes_key():
    client = FakeS3Client()
    MenuStorage(client=client, bucket='bucket').delete('images/a.webp')
    assert client.calls == [('delete', {'Bucket': 'bucket', 'Key': 'menu/images/a.webp'})]


def test_list_returns_relative_keys():
    client = FakeS3Client(keys=['menu/images/a.webp', 'menu/menu.json', 'absence-attachments/x.pdf'])
    assert MenuStorage(client=client, bucket='bucket').list('images/') == ['images/a.webp']


def test_requires_bucket(monkeypatch):
    monkeypatch.delenv('AWS_S3_BUCKET_NAME', raising=False)
    with pytest.raises(ValueError):
        MenuStorage(client=FakeS3Client())


def test_public_url(monkeypatch):
    monkeypatch.setenv('MENU_PUBLIC_BASE_URL', 'https://cdn.test/menu/')
    assert public_url('images/a.webp') == 'https://cdn.test/menu/images/a.webp'
    assert public_url(None) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_menu_storage.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.utils.menu_storage'`

- [ ] **Step 3: Write implementation**

`backend/app/utils/menu_storage.py`:

```python
import os

import boto3

PREFIX = 'menu/'


def public_url(rel_key):
    if not rel_key:
        return None
    base = os.getenv('MENU_PUBLIC_BASE_URL', '').rstrip('/')
    return f'{base}/{rel_key}'


class MenuStorage:
    """Acceso a S3 limitado al prefijo público `menu/` del bucket existente."""

    def __init__(self, client=None, bucket=None):
        self.bucket = bucket or os.getenv('AWS_S3_BUCKET_NAME')
        if not self.bucket:
            raise ValueError('AWS_S3_BUCKET_NAME no está configurado')
        self.client = client or boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
        )

    @staticmethod
    def full_key(rel_key):
        rel = (rel_key or '').lstrip('/')
        if not rel or '..' in rel.split('/'):
            raise ValueError(f'Clave inválida para la carta: {rel_key!r}')
        return PREFIX + rel

    def put(self, rel_key, body, content_type, cache_control):
        self.client.put_object(
            Bucket=self.bucket,
            Key=self.full_key(rel_key),
            Body=body,
            ContentType=content_type,
            CacheControl=cache_control,
        )

    def delete(self, rel_key):
        self.client.delete_object(Bucket=self.bucket, Key=self.full_key(rel_key))

    def list(self, rel_prefix):
        paginator = self.client.get_paginator('list_objects_v2')
        keys = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=self.full_key(rel_prefix)):
            for obj in page.get('Contents', []):
                keys.append(obj['Key'][len(PREFIX):])
        return keys


def get_menu_storage():
    """Storage de la app actual; los tests inyectan uno falso en app.extensions['menu_storage']."""
    from flask import current_app
    return current_app.extensions.get('menu_storage') or MenuStorage()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_menu_storage.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/utils/menu_storage.py backend/tests/test_menu_storage.py
git commit -m "feat(menu): add S3 storage restricted to public menu/ prefix"
```

---

### Task 3: Modelos, migración y fixtures de test

**Files:**
- Create: `backend/app/models/menu.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/migrations/versions/add_menu_tables.py`
- Create: `backend/tests/menu_fakes.py`, `backend/tests/conftest.py`
- Test: `backend/tests/test_menu_models.py`

- [ ] **Step 1: Crear fakes y fixtures compartidos**

`backend/tests/menu_fakes.py`:

```python
class FakeStorage:
    """Reemplazo en memoria de MenuStorage."""

    def __init__(self):
        self.objects = {}

    def put(self, rel_key, body, content_type, cache_control):
        self.objects[rel_key] = {'body': body, 'content_type': content_type, 'cache_control': cache_control}

    def delete(self, rel_key):
        self.objects.pop(rel_key, None)

    def list(self, rel_prefix):
        return sorted(k for k in self.objects if k.startswith(rel_prefix))


class FakeFudoClient:
    def __init__(self, products=None, categories=None):
        self.products = products or []
        self.categories = categories or []

    def get_all_products(self):
        return self.products

    def get_all_product_categories(self):
        return self.categories


def fudo_product(fudo_id, name, price, active=True, category_id='1'):
    return {
        'id': str(fudo_id),
        'type': 'Product',
        'attributes': {'name': name, 'price': price, 'active': active},
        'relationships': {'productCategory': {'data': {'id': category_id, 'type': 'ProductCategory'}}},
    }


def fudo_category(category_id, name):
    return {'id': str(category_id), 'type': 'ProductCategory', 'attributes': {'name': name}}
```

`backend/tests/conftest.py`:

```python
import pytest

from app import create_app
from app.extensions import db
from app.models.user import User
from menu_fakes import FakeStorage


@pytest.fixture
def menu_app(monkeypatch):
    monkeypatch.setenv('MENU_PUBLIC_BASE_URL', 'https://cdn.test/menu')
    app = create_app('testing')
    app.extensions['menu_storage'] = FakeStorage()
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def menu_client(menu_app):
    return menu_app.test_client()


@pytest.fixture
def storage(menu_app):
    return menu_app.extensions['menu_storage']


def _login_headers(client, email, role):
    user = User(email=email, role=role, is_active=True)
    user.set_password('secret123')
    db.session.add(user)
    db.session.commit()
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': 'secret123'})
    return {'Authorization': f"Bearer {response.get_json()['access_token']}"}


@pytest.fixture
def admin_headers(menu_client):
    return _login_headers(menu_client, 'menu-admin@test.com', 'admin')


@pytest.fixture
def employee_headers(menu_client):
    return _login_headers(menu_client, 'menu-employee@test.com', 'employee')
```

> Los fixtures de los tests existentes (`app`, `client`, …) tienen otros nombres y se definen en cada archivo, así que no hay conflicto.

- [ ] **Step 2: Write the failing test**

`backend/tests/test_menu_models.py`:

```python
from decimal import Decimal

from app.extensions import db
from app.models.menu import MenuCategory, MenuItem, MenuItemVariant, MenuTag, MenuSetting, FudoProduct


def _category(name='Cafés', slug='cafes', order=0):
    category = MenuCategory(name=name, slug=slug, sort_order=order)
    db.session.add(category)
    db.session.flush()
    return category


def test_items_are_ordered_and_serialized(menu_app):
    category = _category()
    tag = MenuTag(name='Sin TACC', slug='sin-tacc', color='#7FA34A')
    second = MenuItem(category_id=category.id, name='Capuchino', sort_order=1)
    first = MenuItem(category_id=category.id, name='Latte', sort_order=0, image_key='images/a.webp', tags=[tag])
    first.variants = [MenuItemVariant(label=None, price=Decimal('6900'), sort_order=0)]
    db.session.add_all([tag, second, first])
    db.session.commit()

    data = category.to_dict(include_items=True)
    assert [i['name'] for i in data['items']] == ['Latte', 'Capuchino']
    latte = data['items'][0]
    assert latte['image_url'] == 'https://cdn.test/menu/images/a.webp'
    assert latte['tag_ids'] == [tag.id]
    assert latte['variants'][0]['price'] == 6900.0
    assert latte['variants'][0]['fudo_product_id'] is None


def test_deleting_item_deletes_variants(menu_app):
    category = _category()
    item = MenuItem(category_id=category.id, name='Torta Galia')
    item.variants = [MenuItemVariant(label='Porción', price=11200), MenuItemVariant(label='Entera', price=12600)]
    db.session.add(item)
    db.session.commit()

    db.session.delete(item)
    db.session.commit()
    assert MenuItemVariant.query.count() == 0


def test_menu_setting_get_and_set(menu_app):
    assert MenuSetting.get('footer_text', 'default') == 'default'
    MenuSetting.set('footer_text', '¡Que disfrutes!')
    db.session.commit()
    MenuSetting.set('footer_text', 'Otro texto')
    db.session.commit()
    assert MenuSetting.get('footer_text') == 'Otro texto'
    assert MenuSetting.query.count() == 1


def test_fudo_product_to_dict(menu_app):
    product = FudoProduct(fudo_id='42', name='Latte Vainilla', price=Decimal('6900'), category_name='Cafetería', is_active=True)
    db.session.add(product)
    db.session.commit()
    assert product.to_dict() == {
        'fudo_id': '42', 'name': 'Latte Vainilla', 'price': 6900.0,
        'category_name': 'Cafetería', 'is_active': True, 'ignored': False,
    }
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && pytest tests/test_menu_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.models.menu'`

- [ ] **Step 4: Write models**

`backend/app/models/menu.py`:

```python
from datetime import datetime

from app.extensions import db
from app.utils.menu_storage import public_url

menu_item_tags = db.Table(
    'menu_item_tags',
    db.Column('item_id', db.Integer, db.ForeignKey('menu_items.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('menu_tags.id', ondelete='CASCADE'), primary_key=True),
)


class MenuCategory(db.Model):
    __tablename__ = 'menu_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship(
        'MenuItem',
        backref='category',
        order_by=lambda: [MenuItem.sort_order, MenuItem.id],
        cascade='all, delete-orphan',
    )

    def to_dict(self, include_items=False):
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_visible': self.is_visible,
        }
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        return data


class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('menu_categories.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_key = db.Column(db.String(300))
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants = db.relationship(
        'MenuItemVariant',
        backref='item',
        order_by=lambda: [MenuItemVariant.sort_order, MenuItemVariant.id],
        cascade='all, delete-orphan',
    )
    tags = db.relationship('MenuTag', secondary=menu_item_tags, backref='items')

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'image_key': self.image_key,
            'image_url': public_url(self.image_key),
            'sort_order': self.sort_order,
            'is_visible': self.is_visible,
            'is_featured': self.is_featured,
            'tag_ids': sorted(tag.id for tag in self.tags),
            'variants': [variant.to_dict() for variant in self.variants],
        }


class MenuItemVariant(db.Model):
    __tablename__ = 'menu_item_variants'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id', ondelete='CASCADE'), nullable=False, index=True)
    label = db.Column(db.String(100))
    fudo_product_id = db.Column(db.String(20), unique=True)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    fudo_status = db.Column(db.String(20))  # 'ok' | 'inactive' | 'missing' | None (no vinculada)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'fudo_product_id': self.fudo_product_id,
            'price': float(self.price),
            'fudo_status': self.fudo_status,
            'sort_order': self.sort_order,
        }


class MenuTag(db.Model):
    __tablename__ = 'menu_tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(60), nullable=False, unique=True)
    color = db.Column(db.String(7), nullable=False, default='#5C2E46')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'slug': self.slug, 'color': self.color}


class FudoProduct(db.Model):
    """Caché de productos de Fudo, actualizada por la sincronización."""
    __tablename__ = 'fudo_products'

    fudo_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    category_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    ignored = db.Column(db.Boolean, nullable=False, default=False)
    synced_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'fudo_id': self.fudo_id,
            'name': self.name,
            'price': float(self.price),
            'category_name': self.category_name,
            'is_active': self.is_active,
            'ignored': bool(self.ignored),
        }


class MenuSetting(db.Model):
    __tablename__ = 'menu_settings'

    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text)

    @classmethod
    def get(cls, key, default=None):
        setting = db.session.get(cls, key)
        return setting.value if setting is not None else default

    @classmethod
    def set(cls, key, value):
        setting = db.session.get(cls, key)
        if setting is None:
            setting = cls(key=key)
            db.session.add(setting)
        setting.value = value
        return setting
```

- [ ] **Step 5: Exportar modelos**

En `backend/app/models/__init__.py`, agregar después de `from app.models.employee_document import EmployeeDocument`:

```python
from app.models.menu import MenuCategory, MenuItem, MenuItemVariant, MenuTag, FudoProduct, MenuSetting
```

y al final de la lista `__all__` (después de `'EmployeeDocument'`, agregando la coma):

```python
    'EmployeeDocument',
    'MenuCategory',
    'MenuItem',
    'MenuItemVariant',
    'MenuTag',
    'FudoProduct',
    'MenuSetting'
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && pytest tests/test_menu_models.py -v`
Expected: 4 passed

- [ ] **Step 7: Write migration**

Verificar el head actual: `cd backend && flask db heads`. Expected: `merge_heads_march8 (head)`. Si el head es otro (por ejemplo porque se mergeó `feature/suppliers`), usar ese valor en `down_revision`.

`backend/migrations/versions/add_menu_tables.py`:

```python
"""Add digital menu (carta) tables

Revision ID: add_menu_tables
Revises: merge_heads_march8
Create Date: 2026-10-07

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_menu_tables'
down_revision = 'merge_heads_march8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'menu_categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(120), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        'menu_tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('slug', sa.String(60), nullable=False, unique=True),
        sa.Column('color', sa.String(7), nullable=False, server_default='#5C2E46'),
    )
    op.create_table(
        'fudo_products',
        sa.Column('fudo_id', sa.String(20), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('category_name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('ignored', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('synced_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        'menu_settings',
        sa.Column('key', sa.String(50), primary_key=True),
        sa.Column('value', sa.Text(), nullable=True),
    )
    op.create_table(
        'menu_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('menu_categories.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_key', sa.String(300), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_menu_items_category_id', 'menu_items', ['category_id'])
    op.create_table(
        'menu_item_variants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('menu_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('label', sa.String(100), nullable=True),
        sa.Column('fudo_product_id', sa.String(20), nullable=True, unique=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('fudo_status', sa.String(20), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_menu_item_variants_item_id', 'menu_item_variants', ['item_id'])
    op.create_table(
        'menu_item_tags',
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('menu_items.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('menu_tags.id', ondelete='CASCADE'), primary_key=True),
    )


def downgrade():
    op.drop_table('menu_item_tags')
    op.drop_index('ix_menu_item_variants_item_id', table_name='menu_item_variants')
    op.drop_table('menu_item_variants')
    op.drop_index('ix_menu_items_category_id', table_name='menu_items')
    op.drop_table('menu_items')
    op.drop_table('menu_settings')
    op.drop_table('fudo_products')
    op.drop_table('menu_tags')
    op.drop_table('menu_categories')
```

- [ ] **Step 8: Aplicar la migración en la base local**

Run: `cd backend && flask db upgrade && flask db current`
Expected: termina con `add_menu_tables (head)`.

Run: `cd backend && flask db downgrade && flask db upgrade`
Expected: sin errores (valida el downgrade).

- [ ] **Step 9: Commit**

```bash
git add backend/app/models/menu.py backend/app/models/__init__.py backend/migrations/versions/add_menu_tables.py backend/tests/menu_fakes.py backend/tests/conftest.py backend/tests/test_menu_models.py
git commit -m "feat(menu): add menu models, migration and test fixtures"
```

---

### Task 4: Productos en el cliente de Fudo

**Files:**
- Modify: `backend/app/utils/fudo_client.py` (agregar métodos al final de la clase `FudoClient`)
- Test: `backend/tests/test_fudo_client_products.py`

Referencia API: `GET /products` y `GET /product-categories` en `https://api.fu.do/v1alpha1/openapi.yml`. Paginado con `page[size]` (máx. 500) y `page[number]`. Respuesta JSON:API: `data[].id`, `data[].attributes.{name, price, active, ...}`, `data[].relationships.productCategory.data.id`.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_fudo_client_products.py`:

```python
from app.utils.fudo_client import FudoClient


def _client_with_pages(monkeypatch, pages_by_endpoint):
    client = FudoClient(api_key='key', api_secret='secret')
    calls = []

    def fake_request(endpoint, params=None):
        calls.append((endpoint, params))
        pages = pages_by_endpoint[endpoint]
        index = params['page[number]'] - 1
        return {'data': pages[index] if index < len(pages) else []}

    monkeypatch.setattr(client, '_make_request', fake_request)
    return client, calls


def test_get_all_products_paginates_until_short_page(monkeypatch):
    full_page = [{'id': str(i)} for i in range(500)]
    client, calls = _client_with_pages(monkeypatch, {'/products': [full_page, [{'id': '500'}]]})

    products = client.get_all_products()

    assert len(products) == 501
    assert [c[1]['page[number]'] for c in calls] == [1, 2]
    assert calls[0] == ('/products', {'page[size]': 500, 'page[number]': 1})


def test_get_all_product_categories(monkeypatch):
    client, calls = _client_with_pages(monkeypatch, {'/product-categories': [[{'id': '1'}, {'id': '2'}]]})

    assert [c['id'] for c in client.get_all_product_categories()] == ['1', '2']
    assert calls[0][0] == '/product-categories'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_fudo_client_products.py -v`
Expected: FAIL with `AttributeError: 'FudoClient' object has no attribute 'get_all_products'`

- [ ] **Step 3: Write implementation**

Agregar al final de la clase `FudoClient` en `backend/app/utils/fudo_client.py`:

```python
    def get_products(self, page_size: int = 500, page_number: int = 1) -> Dict:
        """Get a page of products from Fudo API"""
        params = {'page[size]': min(page_size, 500), 'page[number]': page_number}
        return self._make_request('/products', params)

    def get_product_categories(self, page_size: int = 500, page_number: int = 1) -> Dict:
        """Get a page of product categories from Fudo API"""
        params = {'page[size]': min(page_size, 500), 'page[number]': page_number}
        return self._make_request('/product-categories', params)

    def get_all_products(self) -> List[Dict]:
        """Get all products (active and inactive), following pagination"""
        return self._get_all_pages(self.get_products)

    def get_all_product_categories(self) -> List[Dict]:
        """Get all product categories, following pagination"""
        return self._get_all_pages(self.get_product_categories)

    def _get_all_pages(self, fetch_page, page_size: int = 500) -> List[Dict]:
        items = []
        page_number = 1
        while True:
            data = fetch_page(page_size=page_size, page_number=page_number).get('data', [])
            items.extend(data)
            if len(data) < page_size:
                return items
            page_number += 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_fudo_client_products.py -v`
Expected: 2 passed

- [ ] **Step 5: Verificar contra la API real (manual)**

Con `FUDO_API_KEY` y `FUDO_API_SECRET` en `backend/.env`:

```bash
cd backend && python -c "from dotenv import load_dotenv; load_dotenv(); from app.utils.fudo_client import FudoClient; c=FudoClient(); p=c.get_all_products(); print(len(p)); print(p[0])"
```

Expected: cantidad de productos > 0 y un producto con `attributes.name`, `attributes.price`, `attributes.active` y `relationships.productCategory.data.id`. **Si `relationships.productCategory` no aparece**, cambiar en `get_products` los params a `{'page[size]': ..., 'page[number]': ..., 'include': 'productCategory'}` y volver a correr Step 4 actualizando el `assert calls[0] == ...` del test.

- [ ] **Step 6: Commit**

```bash
git add backend/app/utils/fudo_client.py backend/tests/test_fudo_client_products.py
git commit -m "feat(fudo): fetch products and product categories"
```

---

### Task 5: Servicio de sincronización con Fudo

**Files:**
- Create: `backend/app/services/menu_sync_service.py`
- Test: `backend/tests/test_menu_sync.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_menu_sync.py`:

```python
from decimal import Decimal

import pytest

from app.extensions import db
from app.models.menu import FudoProduct, MenuCategory, MenuItem, MenuItemVariant
from app.services.menu_sync_service import sync_fudo_products, unassigned_products, alert_variants
from menu_fakes import FakeFudoClient, fudo_product, fudo_category


def _item_with_variant(fudo_id, price):
    category = MenuCategory(name='Cafés', slug='cafes')
    db.session.add(category)
    db.session.flush()
    item = MenuItem(category_id=category.id, name='Latte')
    variant = MenuItemVariant(fudo_product_id=fudo_id, price=Decimal(price), fudo_status='ok')
    item.variants = [variant]
    db.session.add(item)
    db.session.commit()
    return item, variant


def test_sync_caches_products_with_category_names(menu_app):
    client = FakeFudoClient(
        products=[fudo_product(1, 'Latte', 6900, category_id='10')],
        categories=[fudo_category(10, 'Cafetería')],
    )
    stats = sync_fudo_products(client)

    product = db.session.get(FudoProduct, '1')
    assert product.name == 'Latte'
    assert product.price == Decimal('6900')
    assert product.category_name == 'Cafetería'
    assert stats == {'products': 1, 'price_changes': 0, 'alerts': 0}


def test_sync_updates_linked_variant_price(menu_app):
    _, variant = _item_with_variant('1', '6500')
    stats = sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]))

    assert variant.price == Decimal('6900')
    assert variant.fudo_status == 'ok'
    assert stats['price_changes'] == 1


def test_sync_flags_inactive_and_missing_products(menu_app):
    _, inactive_variant = _item_with_variant('1', '6900')
    item2 = MenuItem(category_id=inactive_variant.item.category_id, name='Moka')
    missing_variant = MenuItemVariant(fudo_product_id='2', price=Decimal('7000'), fudo_status='ok')
    item2.variants = [missing_variant]
    db.session.add(item2)
    db.session.commit()

    stats = sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900, active=False)]))

    assert inactive_variant.fudo_status == 'inactive'
    assert missing_variant.fudo_status == 'missing'
    assert stats['alerts'] == 2
    assert {v.id for v in alert_variants()} == {inactive_variant.id, missing_variant.id}


def test_sync_never_creates_or_deletes_menu_items(menu_app):
    _item_with_variant('1', '6900')
    sync_fudo_products(FakeFudoClient(products=[fudo_product(2, 'Nuevo', 100)]))
    assert MenuItem.query.count() == 1
    assert MenuItemVariant.query.count() == 1


def test_sync_removes_products_no_longer_in_fudo(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'A', 1), fudo_product(2, 'B', 2)]))
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'A', 1)]))
    assert [p.fudo_id for p in FudoProduct.query.all()] == ['1']


def test_sync_keeps_ignored_flag(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'A', 1)]))
    db.session.get(FudoProduct, '1').ignored = True
    db.session.commit()
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'A', 2)]))
    assert db.session.get(FudoProduct, '1').ignored is True


def test_sync_refuses_empty_product_list(menu_app):
    _item_with_variant('1', '6900')
    with pytest.raises(ValueError):
        sync_fudo_products(FakeFudoClient(products=[]))
    assert MenuItemVariant.query.first().fudo_status == 'ok'


def test_unassigned_excludes_linked_ignored_and_inactive(menu_app):
    sync_fudo_products(FakeFudoClient(products=[
        fudo_product(1, 'Vinculado', 1),
        fudo_product(2, 'Ignorado', 1),
        fudo_product(3, 'Inactivo', 1, active=False),
        fudo_product(4, 'Libre', 1),
    ]))
    _item_with_variant('1', '1')
    db.session.get(FudoProduct, '2').ignored = True
    db.session.commit()

    assert [p.fudo_id for p in unassigned_products()] == ['4']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_menu_sync.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.menu_sync_service'`

- [ ] **Step 3: Write implementation**

`backend/app/services/menu_sync_service.py`:

```python
from datetime import datetime
from decimal import Decimal

from app.extensions import db
from app.models.menu import FudoProduct, MenuItemVariant


def _category_id(product):
    relationship = (product.get('relationships') or {}).get('productCategory') or {}
    return (relationship.get('data') or {}).get('id')


def sync_fudo_products(client):
    """Actualiza la caché de productos de Fudo y los precios/estados de las variantes vinculadas.

    Nunca crea, borra ni mueve ítems de la carta.
    """
    raw_products = client.get_all_products()
    if not raw_products:
        raise ValueError('Fudo no devolvió productos; no se sincronizó nada')

    category_names = {
        str(c['id']): (c.get('attributes') or {}).get('name')
        for c in client.get_all_product_categories()
    }
    existing = {p.fudo_id: p for p in FudoProduct.query.all()}
    now = datetime.utcnow()
    by_id = {}

    for raw in raw_products:
        fudo_id = str(raw['id'])
        attrs = raw.get('attributes') or {}
        product = existing.get(fudo_id)
        if product is None:
            product = FudoProduct(fudo_id=fudo_id, ignored=False)
            db.session.add(product)
        product.name = (attrs.get('name') or '')[:100]
        product.price = Decimal(str(attrs.get('price') or 0))
        product.is_active = bool(attrs.get('active', True))
        product.category_name = category_names.get(str(_category_id(raw)))
        product.synced_at = now
        by_id[fudo_id] = product

    for fudo_id, product in existing.items():
        if fudo_id not in by_id:
            db.session.delete(product)

    price_changes = 0
    alerts = 0
    linked = MenuItemVariant.query.filter(MenuItemVariant.fudo_product_id.isnot(None)).all()
    for variant in linked:
        product = by_id.get(variant.fudo_product_id)
        if product is None:
            variant.fudo_status = 'missing'
        elif not product.is_active:
            variant.fudo_status = 'inactive'
        else:
            variant.fudo_status = 'ok'
            if Decimal(variant.price) != product.price:
                variant.price = product.price
                price_changes += 1
        if variant.fudo_status != 'ok':
            alerts += 1

    db.session.commit()
    return {'products': len(by_id), 'price_changes': price_changes, 'alerts': alerts}


def linked_fudo_ids():
    rows = db.session.query(MenuItemVariant.fudo_product_id).filter(MenuItemVariant.fudo_product_id.isnot(None))
    return {fudo_id for (fudo_id,) in rows}


def unassigned_products():
    linked = linked_fudo_ids()
    products = (
        FudoProduct.query
        .filter(FudoProduct.is_active.is_(True), FudoProduct.ignored.is_(False))
        .order_by(FudoProduct.category_name, FudoProduct.name)
        .all()
    )
    return [p for p in products if p.fudo_id not in linked]


def alert_variants():
    return MenuItemVariant.query.filter(MenuItemVariant.fudo_status.in_(['inactive', 'missing'])).all()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_menu_sync.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/menu_sync_service.py backend/tests/test_menu_sync.py
git commit -m "feat(menu): sync Fudo products and linked variant prices"
```

---

### Task 6: Snapshot y publicación

**Files:**
- Create: `backend/app/services/menu_publish_service.py`
- Test: `backend/tests/test_menu_publish.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_menu_publish.py`:

```python
import json
from decimal import Decimal

from app.extensions import db
from app.models.menu import MenuCategory, MenuItem, MenuItemVariant, MenuTag, MenuSetting
from app.services.menu_publish_service import build_snapshot, has_unpublished_changes, publish


def _seed():
    tag = MenuTag(name='Sin TACC', slug='sin-tacc', color='#7FA34A')
    unused_tag = MenuTag(name='Vegano', slug='vegano', color='#000000')
    cafes = MenuCategory(name='Cafés', slug='cafes', sort_order=1, description='Contanos si lo preferís con azúcar')
    tortas = MenuCategory(name='Tortas', slug='tortas', sort_order=0)
    hidden = MenuCategory(name='Oculta', slug='oculta', sort_order=2, is_visible=False)
    empty = MenuCategory(name='Vacía', slug='vacia', sort_order=3)
    db.session.add_all([tag, unused_tag, cafes, tortas, hidden, empty])
    db.session.flush()

    latte = MenuItem(category_id=cafes.id, name='Latte', sort_order=0, is_featured=True, tags=[tag], image_key='images/latte.webp')
    latte.variants = [MenuItemVariant(price=Decimal('6900'))]
    secret = MenuItem(category_id=cafes.id, name='Secreto', sort_order=1, is_visible=False)
    secret.variants = [MenuItemVariant(price=Decimal('1'))]
    torta = MenuItem(category_id=tortas.id, name='Torta Galia', description='Masa de nuez')
    torta.variants = [
        MenuItemVariant(label='Porción', price=Decimal('11200'), sort_order=0),
        MenuItemVariant(label='Entera', price=Decimal('12600.50'), sort_order=1),
    ]
    in_hidden = MenuItem(category_id=hidden.id, name='No se ve')
    db.session.add_all([latte, secret, torta, in_hidden])
    MenuSetting.set('footer_text', '¡Que disfrutes tu estadía!')
    db.session.commit()


def test_build_snapshot_shape(menu_app):
    _seed()
    snapshot = build_snapshot()

    assert snapshot['version'] == 1
    assert snapshot['settings'] == {'footer_text': '¡Que disfrutes tu estadía!', 'instagram': ''}
    assert snapshot['tags'] == [{'slug': 'sin-tacc', 'name': 'Sin TACC', 'color': '#7FA34A'}]
    assert [c['slug'] for c in snapshot['categories']] == ['tortas', 'cafes']

    tortas, cafes = snapshot['categories']
    assert tortas['items'][0]['variants'] == [
        {'label': 'Porción', 'price': 11200},
        {'label': 'Entera', 'price': 12600.5},
    ]
    assert cafes['description'] == 'Contanos si lo preferís con azúcar'
    assert [i['name'] for i in cafes['items']] == ['Latte']
    latte = cafes['items'][0]
    assert latte['featured'] is True
    assert latte['tags'] == ['sin-tacc']
    assert latte['image'] == 'https://cdn.test/menu/images/latte.webp'
    assert 'published_at' not in snapshot


def test_publish_uploads_json_and_clears_pending_flag(menu_app, storage):
    _seed()
    assert has_unpublished_changes() is True

    result = publish(storage)

    stored = storage.objects['menu.json']
    assert stored['content_type'] == 'application/json; charset=utf-8'
    assert stored['cache_control'] == 'public, max-age=60'
    payload = json.loads(stored['body'].decode('utf-8'))
    assert payload['published_at'] == result['published_at']
    assert MenuSetting.get('last_published_at') == result['published_at']
    assert has_unpublished_changes() is False


def test_changes_after_publish_are_detected(menu_app, storage):
    _seed()
    publish(storage)
    MenuItem.query.filter_by(name='Latte').one().name = 'Latte grande'
    db.session.commit()
    assert has_unpublished_changes() is True


def test_publish_deletes_orphan_images_only(menu_app, storage):
    _seed()
    storage.put('images/latte.webp', b'x', 'image/webp', 'c')
    storage.put('images/old.webp', b'x', 'image/webp', 'c')
    publish(storage)
    assert storage.list('images/') == ['images/latte.webp']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_menu_publish.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.menu_publish_service'`

- [ ] **Step 3: Write implementation**

`backend/app/services/menu_publish_service.py`:

```python
import hashlib
import json
from datetime import datetime

from app.extensions import db
from app.models.menu import MenuCategory, MenuItem, MenuTag, MenuSetting
from app.utils.menu_storage import public_url

SNAPSHOT_VERSION = 1


def _price(value):
    number = float(value)
    return int(number) if number.is_integer() else number


def build_snapshot():
    """Arma el contenido público de la carta (sin `published_at`)."""
    categories = []
    used_tags = set()
    visible_categories = (
        MenuCategory.query.filter_by(is_visible=True)
        .order_by(MenuCategory.sort_order, MenuCategory.id)
        .all()
    )
    for category in visible_categories:
        items = []
        for item in category.items:
            if not item.is_visible:
                continue
            tag_slugs = sorted(tag.slug for tag in item.tags)
            used_tags.update(tag_slugs)
            items.append({
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'image': public_url(item.image_key),
                'featured': bool(item.is_featured),
                'tags': tag_slugs,
                'variants': [{'label': v.label, 'price': _price(v.price)} for v in item.variants],
            })
        if items:
            categories.append({
                'slug': category.slug,
                'name': category.name,
                'description': category.description,
                'items': items,
            })

    tags = [
        {'slug': tag.slug, 'name': tag.name, 'color': tag.color}
        for tag in MenuTag.query.order_by(MenuTag.name).all()
        if tag.slug in used_tags
    ]
    return {
        'version': SNAPSHOT_VERSION,
        'settings': {
            'footer_text': MenuSetting.get('footer_text', '') or '',
            'instagram': MenuSetting.get('instagram', '') or '',
        },
        'tags': tags,
        'categories': categories,
    }


def snapshot_hash(snapshot):
    encoded = json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def has_unpublished_changes():
    return MenuSetting.get('last_published_hash') != snapshot_hash(build_snapshot())


def publish(storage):
    snapshot = build_snapshot()
    published_at = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    body = json.dumps({**snapshot, 'published_at': published_at}, ensure_ascii=False).encode('utf-8')
    storage.put('menu.json', body, 'application/json; charset=utf-8', 'public, max-age=60')

    MenuSetting.set('last_published_hash', snapshot_hash(snapshot))
    MenuSetting.set('last_published_at', published_at)
    db.session.commit()

    _delete_orphan_images(storage)
    return {'published_at': published_at}


def _delete_orphan_images(storage):
    referenced = {
        key for (key,) in db.session.query(MenuItem.image_key).filter(MenuItem.image_key.isnot(None))
    }
    for key in storage.list('images/'):
        if key not in referenced:
            storage.delete(key)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_menu_publish.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/menu_publish_service.py backend/tests/test_menu_publish.py
git commit -m "feat(menu): build and publish menu.json snapshot"
```

---

### Task 7: Procesamiento de imágenes

**Files:**
- Create: `backend/app/services/menu_image_service.py`
- Test: `backend/tests/test_menu_image.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_menu_image.py`:

```python
import io

import pytest
from PIL import Image

from app.services.menu_image_service import process_image, InvalidImageError, MAX_UPLOAD_BYTES


def _image_bytes(fmt='PNG', size=(1600, 1200), mode='RGB'):
    buffer = io.BytesIO()
    Image.new(mode, size, color=(200, 100, 50) if mode == 'RGB' else (200, 100, 50, 128)).save(buffer, format=fmt)
    return buffer.getvalue()


def test_converts_to_webp_and_limits_size():
    body, key = process_image(_image_bytes('JPEG'))
    result = Image.open(io.BytesIO(body))
    assert result.format == 'WEBP'
    assert max(result.size) == 800
    assert key.startswith('images/') and key.endswith('.webp')


def test_key_is_content_hash():
    data = _image_bytes('PNG')
    assert process_image(data)[1] == process_image(data)[1]


def test_keeps_transparency():
    body, _ = process_image(_image_bytes('PNG', mode='RGBA'))
    assert Image.open(io.BytesIO(body)).mode == 'RGBA'


def test_rejects_non_images():
    with pytest.raises(InvalidImageError):
        process_image(b'not an image')


def test_rejects_unsupported_format():
    with pytest.raises(InvalidImageError):
        process_image(_image_bytes('GIF', mode='RGB'))


def test_rejects_large_files():
    with pytest.raises(InvalidImageError):
        process_image(b'0' * (MAX_UPLOAD_BYTES + 1))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_menu_image.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.menu_image_service'`

- [ ] **Step 3: Write implementation**

`backend/app/services/menu_image_service.py`:

```python
import hashlib
import io

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_SIDE = 800
ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP'}


class InvalidImageError(ValueError):
    pass


def process_image(data):
    """Valida la imagen, la redimensiona a 800px de lado máximo y la convierte a WebP.

    Devuelve (bytes_webp, clave_relativa) donde la clave es `images/<hash>.webp`.
    """
    if len(data) > MAX_UPLOAD_BYTES:
        raise InvalidImageError('La imagen supera los 10 MB')
    try:
        image = Image.open(io.BytesIO(data))
        image_format = image.format
        image.load()
    except (UnidentifiedImageError, OSError):
        raise InvalidImageError('El archivo no es una imagen válida')
    if image_format not in ALLOWED_FORMATS:
        raise InvalidImageError('Formato no soportado: usá JPG, PNG o WebP')

    image = ImageOps.exif_transpose(image)
    if image.mode not in ('RGB', 'RGBA'):
        has_alpha = 'A' in image.getbands() or 'transparency' in image.info
        image = image.convert('RGBA' if has_alpha else 'RGB')
    image.thumbnail((MAX_SIDE, MAX_SIDE))

    output = io.BytesIO()
    image.save(output, format='WEBP', quality=82, method=6)
    body = output.getvalue()
    return body, f'images/{hashlib.sha256(body).hexdigest()[:16]}.webp'
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_menu_image.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/menu_image_service.py backend/tests/test_menu_image.py
git commit -m "feat(menu): resize and convert menu photos to WebP"
```

---

### Task 8: API admin — árbol, categorías, ítems, tags y configuración

**Files:**
- Create: `backend/app/routes/menu.py`
- Modify: `backend/app/__init__.py` (import y registro del blueprint)
- Test: `backend/tests/test_menu_routes.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_menu_routes.py`:

```python
from decimal import Decimal

from app.extensions import db
from app.models.menu import FudoProduct, MenuItem


def _create_category(client, headers, name='Cafés'):
    response = client.post('/api/v1/menu/categories', json={'name': name}, headers=headers)
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def _create_item(client, headers, category_id, **overrides):
    payload = {'category_id': category_id, 'name': 'Latte', 'variants': [{'label': None, 'price': 6900}]}
    payload.update(overrides)
    return client.post('/api/v1/menu/items', json=payload, headers=headers)


def test_requires_admin(menu_client, employee_headers):
    assert menu_client.get('/api/v1/menu', headers=employee_headers).status_code == 403
    assert menu_client.get('/api/v1/menu').status_code == 401


def test_get_menu_tree_and_status(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    _create_item(menu_client, admin_headers, category['id'])

    data = menu_client.get('/api/v1/menu', headers=admin_headers).get_json()

    assert data['categories'][0]['items'][0]['name'] == 'Latte'
    assert data['status'] == {
        'has_unpublished_changes': True,
        'last_published_at': None,
        'unassigned_count': 0,
        'alerts_count': 0,
    }


def test_category_slugs_are_unique(menu_client, admin_headers):
    first = _create_category(menu_client, admin_headers, 'Cafés')
    second = _create_category(menu_client, admin_headers, 'Cafes')
    assert (first['slug'], second['slug']) == ('cafes', 'cafes-2')
    assert (first['sort_order'], second['sort_order']) == (0, 1)


def test_category_requires_name(menu_client, admin_headers):
    response = menu_client.post('/api/v1/menu/categories', json={'name': '  '}, headers=admin_headers)
    assert response.status_code == 400


def test_update_category(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    response = menu_client.put(f"/api/v1/menu/categories/{category['id']}",
                               json={'name': 'Cafetería', 'is_visible': False, 'description': 'Nota'},
                               headers=admin_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert (data['name'], data['slug'], data['is_visible'], data['description']) == ('Cafetería', 'cafeteria', False, 'Nota')


def test_cannot_delete_category_with_items(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    _create_item(menu_client, admin_headers, category['id'])
    assert menu_client.delete(f"/api/v1/menu/categories/{category['id']}", headers=admin_headers).status_code == 409


def test_delete_empty_category(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    assert menu_client.delete(f"/api/v1/menu/categories/{category['id']}", headers=admin_headers).status_code == 200


def test_reorder_categories(menu_client, admin_headers):
    a = _create_category(menu_client, admin_headers, 'A')
    b = _create_category(menu_client, admin_headers, 'B')
    response = menu_client.put('/api/v1/menu/categories/reorder', json={'ids': [b['id'], a['id']]}, headers=admin_headers)
    assert response.status_code == 200
    names = [c['name'] for c in menu_client.get('/api/v1/menu', headers=admin_headers).get_json()['categories']]
    assert names == ['B', 'A']


def test_reorder_rejects_incomplete_ids(menu_client, admin_headers):
    a = _create_category(menu_client, admin_headers, 'A')
    response = menu_client.put('/api/v1/menu/categories/reorder', json={'ids': [a['id'], 999]}, headers=admin_headers)
    assert response.status_code == 400


def test_create_item_with_manual_price(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    response = _create_item(menu_client, admin_headers, category['id'], description='Con leche')
    data = response.get_json()
    assert response.status_code == 201
    assert data['variants'] == [{'id': data['variants'][0]['id'], 'label': None, 'fudo_product_id': None,
                                 'price': 6900.0, 'fudo_status': None, 'sort_order': 0}]


def test_create_item_validations(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    assert _create_item(menu_client, admin_headers, category['id'], name='').status_code == 400
    assert _create_item(menu_client, admin_headers, 999).status_code == 400
    assert _create_item(menu_client, admin_headers, category['id'], variants=[]).status_code == 400
    assert _create_item(menu_client, admin_headers, category['id'], variants=[{'price': -1}]).status_code == 400
    assert _create_item(menu_client, admin_headers, category['id'], variants=[{'price': 'abc'}]).status_code == 400
    assert MenuItem.query.count() == 0


def test_linked_variant_uses_fudo_price(menu_client, admin_headers):
    db.session.add(FudoProduct(fudo_id='7', name='Latte', price=Decimal('7100'), is_active=True))
    db.session.commit()
    category = _create_category(menu_client, admin_headers)

    response = _create_item(menu_client, admin_headers, category['id'],
                            variants=[{'fudo_product_id': '7', 'price': 1}])

    variant = response.get_json()['variants'][0]
    assert (variant['price'], variant['fudo_product_id'], variant['fudo_status']) == (7100.0, '7', 'ok')


def test_fudo_product_cannot_be_linked_twice(menu_client, admin_headers):
    db.session.add(FudoProduct(fudo_id='7', name='Latte', price=Decimal('7100'), is_active=True))
    db.session.commit()
    category = _create_category(menu_client, admin_headers)
    _create_item(menu_client, admin_headers, category['id'], variants=[{'fudo_product_id': '7'}])

    response = _create_item(menu_client, admin_headers, category['id'], name='Otro', variants=[{'fudo_product_id': '7'}])
    assert response.status_code == 400
    assert 'ya está en otro ítem' in response.get_json()['error']


def test_unknown_fudo_product_is_rejected(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    assert _create_item(menu_client, admin_headers, category['id'], variants=[{'fudo_product_id': '404'}]).status_code == 400


def test_update_item_can_keep_same_fudo_link(menu_client, admin_headers):
    db.session.add(FudoProduct(fudo_id='7', name='Latte', price=Decimal('7100'), is_active=True))
    db.session.commit()
    category = _create_category(menu_client, admin_headers)
    item = _create_item(menu_client, admin_headers, category['id'], variants=[{'fudo_product_id': '7'}]).get_json()

    response = menu_client.put(f"/api/v1/menu/items/{item['id']}", json={
        'name': 'Latte grande',
        'variants': [{'label': 'Grande', 'fudo_product_id': '7'}, {'label': 'Chico', 'price': 5000}],
    }, headers=admin_headers)

    data = response.get_json()
    assert response.status_code == 200
    assert data['name'] == 'Latte grande'
    assert [(v['label'], v['price']) for v in data['variants']] == [('Grande', 7100.0), ('Chico', 5000.0)]


def test_moving_item_to_other_category_appends_it(menu_client, admin_headers):
    a = _create_category(menu_client, admin_headers, 'A')
    b = _create_category(menu_client, admin_headers, 'B')
    _create_item(menu_client, admin_headers, b['id'], name='Existente')
    item = _create_item(menu_client, admin_headers, a['id']).get_json()

    data = menu_client.put(f"/api/v1/menu/items/{item['id']}", json={'category_id': b['id']}, headers=admin_headers).get_json()
    assert (data['category_id'], data['sort_order']) == (b['id'], 1)


def test_reorder_items(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    first = _create_item(menu_client, admin_headers, category['id'], name='Uno').get_json()
    second = _create_item(menu_client, admin_headers, category['id'], name='Dos').get_json()

    response = menu_client.put(f"/api/v1/menu/categories/{category['id']}/items/reorder",
                               json={'ids': [second['id'], first['id']]}, headers=admin_headers)
    assert response.status_code == 200
    items = menu_client.get('/api/v1/menu', headers=admin_headers).get_json()['categories'][0]['items']
    assert [i['name'] for i in items] == ['Dos', 'Uno']


def test_delete_item(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    item = _create_item(menu_client, admin_headers, category['id']).get_json()
    assert menu_client.delete(f"/api/v1/menu/items/{item['id']}", headers=admin_headers).status_code == 200
    assert MenuItem.query.count() == 0


def test_tags_crud_and_assignment(menu_client, admin_headers):
    created = menu_client.post('/api/v1/menu/tags', json={'name': 'Sin TACC', 'color': '#7FA34A'}, headers=admin_headers)
    tag = created.get_json()
    assert created.status_code == 201
    assert tag['slug'] == 'sin-tacc'

    assert menu_client.post('/api/v1/menu/tags', json={'name': 'X', 'color': 'rojo'}, headers=admin_headers).status_code == 400

    category = _create_category(menu_client, admin_headers)
    item = _create_item(menu_client, admin_headers, category['id'], tag_ids=[tag['id']]).get_json()
    assert item['tag_ids'] == [tag['id']]
    assert _create_item(menu_client, admin_headers, category['id'], tag_ids=[999]).status_code == 400

    updated = menu_client.put(f"/api/v1/menu/tags/{tag['id']}", json={'name': 'Apto celíacos'}, headers=admin_headers).get_json()
    assert updated['name'] == 'Apto celíacos'

    assert menu_client.delete(f"/api/v1/menu/tags/{tag['id']}", headers=admin_headers).status_code == 200
    assert MenuItem.query.get(item['id']).tags == []


def test_settings(menu_client, admin_headers):
    assert menu_client.get('/api/v1/menu/settings', headers=admin_headers).get_json() == {'footer_text': '', 'instagram': ''}
    response = menu_client.put('/api/v1/menu/settings',
                               json={'footer_text': '¡Que disfrutes!', 'instagram': '@galia', 'otro': 'x'},
                               headers=admin_headers)
    assert response.get_json() == {'footer_text': '¡Que disfrutes!', 'instagram': '@galia'}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_menu_routes.py -v`
Expected: FAIL — las requests a `/api/v1/menu...` devuelven 404 (blueprint no registrado).

- [ ] **Step 3: Write the blueprint**

`backend/app/routes/menu.py`:

```python
import re
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.menu import FudoProduct, MenuCategory, MenuItem, MenuItemVariant, MenuSetting, MenuTag
from app.services import menu_publish_service, menu_sync_service
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required
from app.utils.slug import unique_slug

bp = Blueprint('menu', __name__, url_prefix='/api/v1/menu')

SETTING_KEYS = ('footer_text', 'instagram')
COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')


def _error(message, status=400):
    return jsonify({'error': message}), status


def _status():
    return {
        'has_unpublished_changes': menu_publish_service.has_unpublished_changes(),
        'last_published_at': MenuSetting.get('last_published_at'),
        'unassigned_count': len(menu_sync_service.unassigned_products()),
        'alerts_count': len(menu_sync_service.alert_variants()),
    }


def _apply_order(model, ids, scope=None):
    """Asigna sort_order según `ids`. Devuelve False si la lista no coincide con los registros."""
    if not isinstance(ids, list) or len(set(ids)) != len(ids):
        return False
    query = model.query.filter(model.id.in_(ids))
    if scope is not None:
        query = query.filter(scope)
    records = {record.id: record for record in query.all()}
    if len(records) != len(ids):
        return False
    for position, record_id in enumerate(ids):
        records[record_id].sort_order = position
    db.session.commit()
    return True


def _next_order(column, *filters):
    current = db.session.query(db.func.max(column)).filter(*filters).scalar()
    return 0 if current is None else current + 1


def _parse_price(value):
    try:
        price = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not price.is_finite() or price < 0:
        return None
    return price


# ---------- Árbol ----------

@bp.route('', methods=['GET'])
@token_required
@admin_required
def get_menu(current_user):
    categories = MenuCategory.query.order_by(MenuCategory.sort_order, MenuCategory.id).all()
    return jsonify({
        'categories': [category.to_dict(include_items=True) for category in categories],
        'tags': [tag.to_dict() for tag in MenuTag.query.order_by(MenuTag.name).all()],
        'status': _status(),
    }), 200


# ---------- Categorías ----------

@bp.route('/categories', methods=['POST'])
@token_required
@admin_required
def create_category(current_user):
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return _error('El nombre es obligatorio')
    category = MenuCategory(
        name=name,
        slug=unique_slug(MenuCategory, name),
        description=(data.get('description') or '').strip() or None,
        is_visible=bool(data.get('is_visible', True)),
        sort_order=_next_order(MenuCategory.sort_order),
    )
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict(include_items=True)), 201


@bp.route('/categories/reorder', methods=['PUT'])
@token_required
@admin_required
def reorder_categories(current_user):
    if not _apply_order(MenuCategory, (request.get_json() or {}).get('ids')):
        return _error('La lista de categorías no es válida')
    return jsonify({'message': 'Orden actualizado'}), 200


@bp.route('/categories/<int:category_id>', methods=['PUT'])
@token_required
@admin_required
def update_category(current_user, category_id):
    category = db.get_or_404(MenuCategory, category_id)
    data = request.get_json() or {}
    if 'name' in data:
        name = (data.get('name') or '').strip()
        if not name:
            return _error('El nombre es obligatorio')
        category.name = name
        category.slug = unique_slug(MenuCategory, name, exclude_id=category.id)
    if 'description' in data:
        category.description = (data.get('description') or '').strip() or None
    if 'is_visible' in data:
        category.is_visible = bool(data['is_visible'])
    db.session.commit()
    return jsonify(category.to_dict(include_items=True)), 200


@bp.route('/categories/<int:category_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_category(current_user, category_id):
    category = db.get_or_404(MenuCategory, category_id)
    if category.items:
        return _error('La categoría tiene ítems: movelos o borralos primero', 409)
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Categoría eliminada'}), 200


@bp.route('/categories/<int:category_id>/items/reorder', methods=['PUT'])
@token_required
@admin_required
def reorder_items(current_user, category_id):
    db.get_or_404(MenuCategory, category_id)
    ids = (request.get_json() or {}).get('ids')
    if not _apply_order(MenuItem, ids, MenuItem.category_id == category_id):
        return _error('La lista de ítems no es válida')
    return jsonify({'message': 'Orden actualizado'}), 200


# ---------- Ítems ----------

def _build_variants(item, variants_data):
    """Valida y construye las variantes. Devuelve (variantes, error)."""
    if not isinstance(variants_data, list) or not variants_data:
        return None, 'El ítem necesita al menos un precio'
    variants = []
    seen_fudo_ids = set()
    for position, raw in enumerate(variants_data):
        raw = raw or {}
        label = (raw.get('label') or '').strip() or None
        fudo_id = str(raw['fudo_product_id']) if raw.get('fudo_product_id') else None
        if fudo_id:
            if fudo_id in seen_fudo_ids:
                return None, 'Un producto de Fudo no puede repetirse en el mismo ítem'
            seen_fudo_ids.add(fudo_id)
            product = db.session.get(FudoProduct, fudo_id)
            if product is None:
                return None, f'Producto de Fudo {fudo_id} no encontrado: sincronizá con Fudo primero'
            taken = MenuItemVariant.query.filter(MenuItemVariant.fudo_product_id == fudo_id)
            if item.id is not None:
                taken = taken.filter(MenuItemVariant.item_id != item.id)
            if taken.first() is not None:
                return None, f'El producto de Fudo "{product.name}" ya está en otro ítem'
            price = product.price
            status = 'ok' if product.is_active else 'inactive'
        else:
            price = _parse_price(raw.get('price'))
            if price is None:
                return None, 'Precio inválido'
            status = None
        variants.append(MenuItemVariant(
            label=label, fudo_product_id=fudo_id, price=price, fudo_status=status, sort_order=position,
        ))
    return variants, None


def _apply_item_payload(item, data):
    """Aplica los campos presentes en `data`. Devuelve un mensaje de error o None."""
    if 'name' in data:
        name = (data.get('name') or '').strip()
        if not name:
            return 'El nombre es obligatorio'
        item.name = name
    if 'description' in data:
        item.description = (data.get('description') or '').strip() or None
    if 'category_id' in data:
        category = db.session.get(MenuCategory, data['category_id']) if data['category_id'] else None
        if category is None:
            return 'Categoría inexistente'
        if item.category_id != category.id:
            item.sort_order = _next_order(MenuItem.sort_order, MenuItem.category_id == category.id)
            item.category_id = category.id
    if 'is_visible' in data:
        item.is_visible = bool(data['is_visible'])
    if 'is_featured' in data:
        item.is_featured = bool(data['is_featured'])
    if 'tag_ids' in data:
        tag_ids = set(data.get('tag_ids') or [])
        tags = MenuTag.query.filter(MenuTag.id.in_(tag_ids)).all() if tag_ids else []
        if len(tags) != len(tag_ids):
            return 'Etiqueta inexistente'
        item.tags = tags
    if 'variants' in data:
        variants, error = _build_variants(item, data['variants'])
        if error:
            return error
        if item.id is not None:
            # Borrar primero para no chocar con el unique de fudo_product_id al re-vincular.
            item.variants.clear()
            db.session.flush()
        item.variants = variants
    return None


@bp.route('/items', methods=['POST'])
@token_required
@admin_required
def create_item(current_user):
    data = request.get_json() or {}
    if 'variants' not in data:
        return _error('El ítem necesita al menos un precio')
    category_id = data.get('category_id')
    category = db.session.get(MenuCategory, category_id) if category_id else None
    if category is None:
        return _error('Categoría inexistente')
    item = MenuItem(
        category_id=category.id,
        name='',
        sort_order=_next_order(MenuItem.sort_order, MenuItem.category_id == category.id),
    )
    payload = {key: value for key, value in data.items() if key != 'category_id'}
    payload.setdefault('name', '')
    error = _apply_item_payload(item, payload)
    if error:
        db.session.rollback()
        return _error(error)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.route('/items/<int:item_id>', methods=['PUT'])
@token_required
@admin_required
def update_item(current_user, item_id):
    item = db.get_or_404(MenuItem, item_id)
    error = _apply_item_payload(item, request.get_json() or {})
    if error:
        db.session.rollback()
        return _error(error)
    db.session.commit()
    return jsonify(item.to_dict()), 200


@bp.route('/items/<int:item_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_item(current_user, item_id):
    item = db.get_or_404(MenuItem, item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Ítem eliminado'}), 200


# ---------- Tags ----------

def _apply_tag_payload(tag, data):
    if 'name' in data:
        name = (data.get('name') or '').strip()
        if not name:
            return 'El nombre es obligatorio'
        tag.name = name
        tag.slug = unique_slug(MenuTag, name, exclude_id=tag.id)
    if 'color' in data:
        if not COLOR_PATTERN.match(data.get('color') or ''):
            return 'Color inválido (formato #RRGGBB)'
        tag.color = data['color']
    return None


@bp.route('/tags', methods=['POST'])
@token_required
@admin_required
def create_tag(current_user):
    data = request.get_json() or {}
    tag = MenuTag(color='#5C2E46')
    error = _apply_tag_payload(tag, {'name': data.get('name'), **({'color': data['color']} if 'color' in data else {})})
    if error:
        return _error(error)
    db.session.add(tag)
    db.session.commit()
    return jsonify(tag.to_dict()), 201


@bp.route('/tags/<int:tag_id>', methods=['PUT'])
@token_required
@admin_required
def update_tag(current_user, tag_id):
    tag = db.get_or_404(MenuTag, tag_id)
    error = _apply_tag_payload(tag, request.get_json() or {})
    if error:
        db.session.rollback()
        return _error(error)
    db.session.commit()
    return jsonify(tag.to_dict()), 200


@bp.route('/tags/<int:tag_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_tag(current_user, tag_id):
    tag = db.get_or_404(MenuTag, tag_id)
    db.session.delete(tag)
    db.session.commit()
    return jsonify({'message': 'Etiqueta eliminada'}), 200


# ---------- Configuración ----------

def _settings():
    return {key: MenuSetting.get(key, '') or '' for key in SETTING_KEYS}


@bp.route('/settings', methods=['GET'])
@token_required
@admin_required
def get_settings(current_user):
    return jsonify(_settings()), 200


@bp.route('/settings', methods=['PUT'])
@token_required
@admin_required
def update_settings(current_user):
    data = request.get_json() or {}
    for key in SETTING_KEYS:
        if key in data:
            MenuSetting.set(key, str(data[key] or '').strip())
    db.session.commit()
    return jsonify(_settings()), 200
```

> Nota de `create_item`: el ítem se agrega a la sesión **después** de validar, así una validación fallida no deja nada pendiente. `unique_slug` y las consultas de `_build_variants` no necesitan el ítem en la sesión.

- [ ] **Step 4: Registrar el blueprint**

En `backend/app/__init__.py`, agregar `menu` al final de la línea de imports de rutas:

```python
    from app.routes import auth, schedules, sales, expenses, reports, employees, shifts, schedule_summary, notifications, coverage, ml_predictions, ml_dashboard, employee_schedule, job_positions, time_tracking, payroll, csv_import, holidays, store_hours, vacation_periods, absence_requests, social_security, employee_documents, fudo_sync, menu
```

y después de `app.register_blueprint(fudo_sync.bp)`:

```python
    app.register_blueprint(menu.bp)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_menu_routes.py -v`
Expected: 20 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/routes/menu.py backend/app/__init__.py backend/tests/test_menu_routes.py
git commit -m "feat(menu): admin API for categories, items, tags and settings"
```

---

### Task 9: API admin — fotos, productos Fudo, bandeja, sync y publicar

**Files:**
- Modify: `backend/app/routes/menu.py` (agregar al final + imports)
- Test: `backend/tests/test_menu_routes_ops.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_menu_routes_ops.py`:

```python
import io
import json
from decimal import Decimal

from PIL import Image

from app.extensions import db
from app.models.menu import FudoProduct, MenuCategory, MenuItem, MenuItemVariant
from menu_fakes import FakeFudoClient, fudo_product


def _item(fudo_id=None, status=None):
    category = MenuCategory(name='Cafés', slug='cafes')
    db.session.add(category)
    db.session.flush()
    item = MenuItem(category_id=category.id, name='Latte')
    item.variants = [MenuItemVariant(price=Decimal('6900'), fudo_product_id=fudo_id, fudo_status=status)]
    db.session.add(item)
    db.session.commit()
    return item


def _png():
    buffer = io.BytesIO()
    Image.new('RGB', (1200, 900), (10, 20, 30)).save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


def test_upload_and_delete_item_image(menu_client, admin_headers, storage):
    item = _item()
    response = menu_client.post(f'/api/v1/menu/items/{item.id}/image',
                                data={'image': (_png(), 'latte.png')},
                                headers=admin_headers, content_type='multipart/form-data')
    data = response.get_json()
    assert response.status_code == 200
    assert data['image_key'] in storage.objects
    assert storage.objects[data['image_key']]['cache_control'] == 'public, max-age=31536000, immutable'
    assert data['image_url'] == f"https://cdn.test/menu/{data['image_key']}"

    deleted = menu_client.delete(f'/api/v1/menu/items/{item.id}/image', headers=admin_headers).get_json()
    assert deleted['image_key'] is None


def test_upload_rejects_invalid_file(menu_client, admin_headers):
    item = _item()
    response = menu_client.post(f'/api/v1/menu/items/{item.id}/image',
                                data={'image': (io.BytesIO(b'nope'), 'x.png')},
                                headers=admin_headers, content_type='multipart/form-data')
    assert response.status_code == 400
    assert menu_client.post(f'/api/v1/menu/items/{item.id}/image', headers=admin_headers).status_code == 400


def test_fudo_products_list_marks_linked_and_filters(menu_client, admin_headers):
    db.session.add_all([
        FudoProduct(fudo_id='1', name='Latte', price=1, is_active=True),
        FudoProduct(fudo_id='2', name='Moka', price=1, is_active=True),
        FudoProduct(fudo_id='3', name='Viejo', price=1, is_active=False),
    ])
    db.session.commit()
    _item(fudo_id='1', status='ok')

    products = menu_client.get('/api/v1/menu/fudo-products', headers=admin_headers).get_json()
    assert [(p['fudo_id'], p['linked']) for p in products] == [('1', True), ('2', False)]

    filtered = menu_client.get('/api/v1/menu/fudo-products?q=MOK', headers=admin_headers).get_json()
    assert [p['fudo_id'] for p in filtered] == ['2']

    unassigned = menu_client.get('/api/v1/menu/fudo-products?unassigned=true', headers=admin_headers).get_json()
    assert [p['fudo_id'] for p in unassigned] == ['2']


def test_ignore_fudo_product(menu_client, admin_headers):
    db.session.add(FudoProduct(fudo_id='2', name='Moka', price=1, is_active=True))
    db.session.commit()
    assert menu_client.post('/api/v1/menu/fudo-products/2/ignore', headers=admin_headers).status_code == 200
    assert db.session.get(FudoProduct, '2').ignored is True
    assert menu_client.post('/api/v1/menu/fudo-products/999/ignore', headers=admin_headers).status_code == 404


def test_inbox(menu_client, admin_headers):
    db.session.add(FudoProduct(fudo_id='2', name='Moka', price=1, is_active=True))
    db.session.commit()
    item = _item(fudo_id='9', status='missing')

    data = menu_client.get('/api/v1/menu/inbox', headers=admin_headers).get_json()
    assert [p['fudo_id'] for p in data['unassigned']] == ['2']
    alert = data['alerts'][0]
    assert (alert['item_id'], alert['item_name'], alert['fudo_status'], alert['fudo_name']) == (item.id, 'Latte', 'missing', None)


def test_sync_endpoint(menu_client, admin_headers, monkeypatch):
    monkeypatch.setattr('app.routes.menu.FudoClient', lambda: FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]))
    data = menu_client.post('/api/v1/menu/sync', headers=admin_headers).get_json()
    assert (data['products'], data['price_changes'], data['alerts']) == (1, 0, 0)
    assert data['status']['unassigned_count'] == 1


def test_sync_endpoint_reports_fudo_errors(menu_client, admin_headers, monkeypatch):
    def broken_client():
        raise ValueError('FUDO_API_KEY and FUDO_API_SECRET must be set')
    monkeypatch.setattr('app.routes.menu.FudoClient', broken_client)
    response = menu_client.post('/api/v1/menu/sync', headers=admin_headers)
    assert response.status_code == 502
    assert 'Fudo' in response.get_json()['error']


def test_publish_endpoint(menu_client, admin_headers, storage):
    _item()
    response = menu_client.post('/api/v1/menu/publish', headers=admin_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data['status']['has_unpublished_changes'] is False
    assert json.loads(storage.objects['menu.json']['body'])['categories'][0]['items'][0]['name'] == 'Latte'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_menu_routes_ops.py -v`
Expected: FAIL — endpoints devuelven 404/405.

- [ ] **Step 3: Write implementation**

En `backend/app/routes/menu.py`, agregar a los imports:

```python
import logging

from app.services.menu_image_service import InvalidImageError, process_image
from app.utils.fudo_client import FudoClient
from app.utils.menu_storage import get_menu_storage
```

y debajo de `bp = Blueprint(...)`:

```python
logger = logging.getLogger(__name__)
```

Agregar al final del archivo:

```python
# ---------- Fotos ----------

@bp.route('/items/<int:item_id>/image', methods=['POST'])
@token_required
@admin_required
def upload_item_image(current_user, item_id):
    item = db.get_or_404(MenuItem, item_id)
    upload = request.files.get('image')
    if upload is None:
        return _error('Falta el archivo "image"')
    try:
        body, key = process_image(upload.read())
    except InvalidImageError as exc:
        return _error(str(exc))
    get_menu_storage().put(key, body, 'image/webp', 'public, max-age=31536000, immutable')
    item.image_key = key
    db.session.commit()
    return jsonify(item.to_dict()), 200


@bp.route('/items/<int:item_id>/image', methods=['DELETE'])
@token_required
@admin_required
def delete_item_image(current_user, item_id):
    item = db.get_or_404(MenuItem, item_id)
    item.image_key = None  # el archivo se borra de S3 al publicar si nadie lo usa
    db.session.commit()
    return jsonify(item.to_dict()), 200


# ---------- Productos de Fudo y bandeja ----------

@bp.route('/fudo-products', methods=['GET'])
@token_required
@admin_required
def list_fudo_products(current_user):
    if request.args.get('unassigned') == 'true':
        products = menu_sync_service.unassigned_products()
    else:
        products = FudoProduct.query.filter_by(is_active=True).order_by(FudoProduct.name).all()
    query = (request.args.get('q') or '').strip().lower()
    if query:
        products = [p for p in products if query in p.name.lower()]
    linked = menu_sync_service.linked_fudo_ids()
    return jsonify([{**p.to_dict(), 'linked': p.fudo_id in linked} for p in products]), 200


@bp.route('/fudo-products/<fudo_id>/ignore', methods=['POST'])
@token_required
@admin_required
def ignore_fudo_product(current_user, fudo_id):
    product = db.get_or_404(FudoProduct, fudo_id)
    product.ignored = True
    db.session.commit()
    return jsonify(product.to_dict()), 200


@bp.route('/inbox', methods=['GET'])
@token_required
@admin_required
def get_inbox(current_user):
    alerts = []
    for variant in menu_sync_service.alert_variants():
        product = db.session.get(FudoProduct, variant.fudo_product_id)
        alerts.append({
            **variant.to_dict(),
            'item_id': variant.item_id,
            'item_name': variant.item.name,
            'fudo_name': product.name if product else None,
        })
    return jsonify({
        'unassigned': [p.to_dict() for p in menu_sync_service.unassigned_products()],
        'alerts': alerts,
    }), 200


# ---------- Sync y publicación ----------

@bp.route('/sync', methods=['POST'])
@token_required
@admin_required
def sync_fudo(current_user):
    try:
        stats = menu_sync_service.sync_fudo_products(FudoClient())
    except Exception as exc:
        db.session.rollback()
        logger.exception('Error sincronizando la carta con Fudo')
        return _error(f'Error sincronizando con Fudo: {exc}', 502)
    return jsonify({**stats, 'status': _status()}), 200


@bp.route('/publish', methods=['POST'])
@token_required
@admin_required
def publish_menu(current_user):
    try:
        result = menu_publish_service.publish(get_menu_storage())
    except Exception as exc:
        db.session.rollback()
        logger.exception('Error publicando la carta')
        return _error(f'Error publicando la carta: {exc}', 502)
    return jsonify({**result, 'status': _status()}), 200
```

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/test_menu_routes_ops.py tests/test_menu_routes.py -v`
Expected: todos pasan (8 + 20).

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/menu.py backend/tests/test_menu_routes_ops.py
git commit -m "feat(menu): photo upload, Fudo inbox, sync and publish endpoints"
```

---

### Task 10: Tarea nocturna de sincronización

**Files:**
- Create: `backend/app/tasks/menu_tasks.py`
- Test: `backend/tests/test_menu_tasks.py`

Regla: tras sincronizar, se republica **solo** si cambió algún precio **y** no había cambios manuales sin publicar antes de la sync (para no publicar borradores de la encargada). Si nunca se publicó, no se publica automáticamente.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_menu_tasks.py`:

```python
from decimal import Decimal

from app.extensions import db
from app.models.menu import MenuCategory, MenuItem, MenuItemVariant
from app.services.menu_publish_service import publish
from app.tasks.menu_tasks import sync_and_publish
from menu_fakes import FakeFudoClient, fudo_product


def _linked_item(price='6500'):
    category = MenuCategory(name='Cafés', slug='cafes')
    db.session.add(category)
    db.session.flush()
    item = MenuItem(category_id=category.id, name='Latte')
    item.variants = [MenuItemVariant(fudo_product_id='1', price=Decimal(price), fudo_status='ok')]
    db.session.add(item)
    db.session.commit()
    return item


def test_republishes_when_prices_change_and_no_drafts(menu_app, storage):
    _linked_item()
    publish(storage)
    storage.objects.pop('menu.json')

    result = sync_and_publish(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]), storage)

    assert result['published'] is True
    assert 'menu.json' in storage.objects


def test_does_not_publish_drafts(menu_app, storage):
    item = _linked_item()
    publish(storage)
    item.name = 'Borrador'
    db.session.commit()
    storage.objects.pop('menu.json')

    result = sync_and_publish(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]), storage)

    assert result['published'] is False
    assert 'menu.json' not in storage.objects


def test_does_not_publish_without_price_changes(menu_app, storage):
    _linked_item('6900')
    publish(storage)
    storage.objects.pop('menu.json')

    assert sync_and_publish(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]), storage)['published'] is False


def test_does_not_publish_if_never_published(menu_app, storage):
    _linked_item()
    assert sync_and_publish(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]), storage)['published'] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_menu_tasks.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.tasks.menu_tasks'`

- [ ] **Step 3: Write implementation**

`backend/app/tasks/menu_tasks.py`:

```python
"""Sincroniza precios de la carta desde Fudo y republica si corresponde.

Uso (cron de Render): cd backend && python -m app.tasks.menu_tasks
"""
import logging

from app.services import menu_publish_service, menu_sync_service

logger = logging.getLogger(__name__)


def sync_and_publish(client, storage):
    had_drafts = menu_publish_service.has_unpublished_changes()
    stats = menu_sync_service.sync_fudo_products(client)
    published = False
    if stats['price_changes'] and not had_drafts:
        menu_publish_service.publish(storage)
        published = True
    return {**stats, 'published': published}


if __name__ == '__main__':
    import os

    from app import create_app
    from app.utils.fudo_client import FudoClient
    from app.utils.menu_storage import get_menu_storage

    logging.basicConfig(level=logging.INFO)
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    with app.app_context():
        logger.info('Sync de carta: %s', sync_and_publish(FudoClient(), get_menu_storage()))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_menu_tasks.py -v`
Expected: 4 passed

- [ ] **Step 5: Correr toda la suite de la carta**

Run: `cd backend && pytest tests/test_menu_*.py tests/test_fudo_client_products.py -v`
Expected: todos pasan.

Run: `cd backend && pytest tests/ -q`
Expected: los tests que ya pasaban en `main` siguen pasando (comparar con `git stash; pytest tests/ -q; git stash pop` si hay dudas).

- [ ] **Step 6: Commit**

```bash
git add backend/app/tasks/menu_tasks.py backend/tests/test_menu_tasks.py
git commit -m "feat(menu): nightly Fudo sync with safe auto-publish"
```

---

### Task 11: Carga inicial desde el PDF

**Files:**
- Create: `backend/data/menu_seed.json`
- Create: `backend/seed_menu.py`

- [ ] **Step 1: Transcribir la carta**

Abrir `Carta_01.pdf` (Drive: `https://drive.google.com/file/d/1xl-DDroZqjhvQLmI2apPupHri9oh8t5a/view`) y recorrer las 7 páginas **mirando cada página** (la extracción de texto pierde la relación plato↔precio). Volcar todo en `backend/data/menu_seed.json` con este formato exacto:

```json
{
  "footer_text": "¡Que disfrutes tu estadía! Si estás con menores es muy importante que sepas que no contamos con servicio de cuidadores, la responsabilidad queda a cargo del adulto que acompaña. También contamos con juegos de mesa para distintas edades, para que todos se diviertan. Estamos a disposición ¡Consultanos!",
  "tags": [
    {"name": "Sin TACC", "color": "#7FA34A"},
    {"name": "Vegano", "color": "#4A7A3A"},
    {"name": "Nuevo", "color": "#E0866A"},
    {"name": "Recomendado", "color": "#5C2E46"}
  ],
  "categories": [
    {
      "name": "Cafés",
      "description": "Contanos si lo preferís con azúcar, stevia o sin nada",
      "items": [
        {"name": "Expresso", "description": null, "tags": [], "variants": [{"label": null, "price": 0}]}
      ]
    },
    {
      "name": "Tortas",
      "description": null,
      "items": [
        {
          "name": "Torta Galia",
          "description": "Masa de nuez rellena de dulce de leche, crema chantilly & corazón de frutos rojos",
          "tags": [],
          "variants": [{"label": "Porción", "price": 0}, {"label": "Entera", "price": 0}]
        }
      ]
    }
  ]
}
```

Reglas de transcripción:
- Categorías en el orden del PDF. Las vistas en el texto extraído son: Cafés, Cafés fríos / Frappé / Matcha, Bebidas frías (limonadas, jugos, agua), Licuados, Laminados, Alfajores, Cookies, Muffins, Opciones saludables, Tortas y postres. Confirmar contra las 7 páginas y agregar las que falten (páginas 4–7).
- Los `0` del ejemplo se reemplazan por el precio real del PDF. Ningún precio puede quedar en `0` al terminar.
- Ítems con dos precios (ej. `$11200 $12600`, "Con gas | Sin gas") → una variante por precio con su `label`.
- Agregados (Vainilla / Caramelo / Avellana) → ítem propio "Syrup" con variantes, o nota en la `description` de la categoría si no tienen precio.
- Notas como "*DIPS: Mantequilla de maní / Dulce de leche / …*" van en la `description` del ítem.
- Nombres en formato título (`Latte Vainilla`, no `LATTE VAINILLA`).

Verificación: `python -c "import json;d=json.load(open('backend/data/menu_seed.json',encoding='utf-8'));p=[v['price'] for c in d['categories'] for i in c['items'] for v in i['variants']];print(len(d['categories']),len(p),min(p))"`
Expected: más de 9 categorías, más de 80 precios y `min > 0`.

- [ ] **Step 2: Write seed script**

`backend/seed_menu.py`:

```python
"""Carga inicial de la carta desde data/menu_seed.json.

Uso: cd backend && python seed_menu.py
No hace nada si ya hay categorías cargadas.
"""
import json
import os
from decimal import Decimal

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.menu import MenuCategory, MenuItem, MenuItemVariant, MenuSetting, MenuTag  # noqa: E402
from app.utils.slug import unique_slug  # noqa: E402

SEED_PATH = os.path.join(os.path.dirname(__file__), 'data', 'menu_seed.json')


def seed(data):
    tags = {}
    for tag_data in data.get('tags', []):
        tag = MenuTag(name=tag_data['name'], slug=unique_slug(MenuTag, tag_data['name']), color=tag_data['color'])
        db.session.add(tag)
        db.session.flush()
        tags[tag.name] = tag

    for category_order, category_data in enumerate(data['categories']):
        category = MenuCategory(
            name=category_data['name'],
            slug=unique_slug(MenuCategory, category_data['name']),
            description=category_data.get('description'),
            sort_order=category_order,
        )
        db.session.add(category)
        db.session.flush()
        for item_order, item_data in enumerate(category_data['items']):
            item = MenuItem(
                category_id=category.id,
                name=item_data['name'],
                description=item_data.get('description'),
                sort_order=item_order,
                tags=[tags[name] for name in item_data.get('tags', [])],
            )
            item.variants = [
                MenuItemVariant(label=v.get('label'), price=Decimal(str(v['price'])), sort_order=position)
                for position, v in enumerate(item_data['variants'])
            ]
            db.session.add(item)

    if data.get('footer_text'):
        MenuSetting.set('footer_text', data['footer_text'])
    db.session.commit()


if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    with app.app_context():
        if MenuCategory.query.first() is not None:
            print('La carta ya tiene categorías; no se cargó nada.')
        else:
            with open(SEED_PATH, encoding='utf-8') as seed_file:
                seed(json.load(seed_file))
            print(f'Carta cargada: {MenuCategory.query.count()} categorías, {MenuItem.query.count()} ítems.')
```

- [ ] **Step 3: Correr el seed en local**

Run: `cd backend && python seed_menu.py`
Expected: `Carta cargada: N categorías, M ítems.` Correrlo otra vez → `La carta ya tiene categorías; no se cargó nada.`

- [ ] **Step 4: Commit**

```bash
git add backend/data/menu_seed.json backend/seed_menu.py
git commit -m "feat(menu): seed initial menu transcribed from Carta_01.pdf"
```

---

## Phase B — Admin en galia-app

No hay runner de tests ni config de ESLint en `frontend/` (`npm run lint` falla por falta de config, es preexistente); cada tarea se verifica con `npm run build` y prueba manual en el navegador contra el backend local (`cd backend && python run.py`, `cd frontend && npm run dev`, login como admin).

### Task 12: Servicio, utilidades, rutas y sidebar

**Files:**
- Create: `frontend/src/services/menuService.js`
- Create: `frontend/src/utils/menuFormat.js`
- Create: `frontend/src/components/menu/ModalShell.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`

- [ ] **Step 1: Servicio**

`frontend/src/services/menuService.js`:

```js
import api from './api'

const menuService = {
  async getMenu() {
    return (await api.get('/menu')).data
  },

  async createCategory(data) {
    return (await api.post('/menu/categories', data)).data
  },

  async updateCategory(id, data) {
    return (await api.put(`/menu/categories/${id}`, data)).data
  },

  async deleteCategory(id) {
    return (await api.delete(`/menu/categories/${id}`)).data
  },

  async reorderCategories(ids) {
    return (await api.put('/menu/categories/reorder', { ids })).data
  },

  async createItem(data) {
    return (await api.post('/menu/items', data)).data
  },

  async updateItem(id, data) {
    return (await api.put(`/menu/items/${id}`, data)).data
  },

  async deleteItem(id) {
    return (await api.delete(`/menu/items/${id}`)).data
  },

  async reorderItems(categoryId, ids) {
    return (await api.put(`/menu/categories/${categoryId}/items/reorder`, { ids })).data
  },

  async uploadItemImage(id, file) {
    const formData = new FormData()
    formData.append('image', file)
    const response = await api.post(`/menu/items/${id}/image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  async deleteItemImage(id) {
    return (await api.delete(`/menu/items/${id}/image`)).data
  },

  async createTag(data) {
    return (await api.post('/menu/tags', data)).data
  },

  async updateTag(id, data) {
    return (await api.put(`/menu/tags/${id}`, data)).data
  },

  async deleteTag(id) {
    return (await api.delete(`/menu/tags/${id}`)).data
  },

  async getSettings() {
    return (await api.get('/menu/settings')).data
  },

  async updateSettings(data) {
    return (await api.put('/menu/settings', data)).data
  },

  async getFudoProducts(params = {}) {
    return (await api.get('/menu/fudo-products', { params })).data
  },

  async ignoreFudoProduct(fudoId) {
    return (await api.post(`/menu/fudo-products/${fudoId}/ignore`)).data
  },

  async getInbox() {
    return (await api.get('/menu/inbox')).data
  },

  async syncFudo() {
    return (await api.post('/menu/sync')).data
  },

  async publish() {
    return (await api.post('/menu/publish')).data
  },
}

export default menuService
```

- [ ] **Step 2: Utilidades**

`frontend/src/utils/menuFormat.js`:

```js
export const formatPrice = (value) =>
  `$${Number(value || 0).toLocaleString('es-AR', { maximumFractionDigits: 2 })}`

export const variantSummary = (variants = []) =>
  variants.map((v) => (v.label ? `${v.label} ${formatPrice(v.price)}` : formatPrice(v.price))).join(' · ')

// Devuelve una copia con los elementos i y j intercambiados, o null si j está fuera de rango.
export const swap = (list, i, j) => {
  if (j < 0 || j >= list.length) return null
  const copy = [...list]
  ;[copy[i], copy[j]] = [copy[j], copy[i]]
  return copy
}

export const normalizeText = (text = '') =>
  text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

export const errorMessage = (err, fallback) => err?.response?.data?.error || fallback

export const PUBLIC_MENU_URL = import.meta.env.VITE_PUBLIC_MENU_URL || 'https://galia-carta.onrender.com'
```

- [ ] **Step 3: Modal reutilizable (pantalla completa en mobile)**

`frontend/src/components/menu/ModalShell.jsx`:

```jsx
import { X } from 'lucide-react'

const ModalShell = ({ title, onClose, children, footer }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-stretch sm:items-center justify-center z-50 sm:p-4">
    <div className="bg-white w-full sm:max-w-xl sm:rounded-lg shadow-xl flex flex-col max-h-screen sm:max-h-[90vh]">
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h2 className="text-lg font-bold text-gray-900">{title}</h2>
        <button type="button" onClick={onClose} className="p-1 text-gray-500 hover:text-gray-700" aria-label="Cerrar">
          <X className="h-5 w-5" />
        </button>
      </div>
      <div className="p-4 overflow-y-auto flex-1">{children}</div>
      {footer && <div className="p-4 border-t border-gray-200 flex flex-wrap gap-2 justify-end">{footer}</div>}
    </div>
  </div>
)

export default ModalShell
```

- [ ] **Step 4: Rutas**

En `frontend/src/App.jsx`, agregar imports después de `import MyDocuments from './pages/MyDocuments'`:

```jsx
import Menu from './pages/Menu'
import MenuInbox from './pages/MenuInbox'
```

y rutas después de `<Route path="/vacation-periods" element={<VacationPeriods />} />`:

```jsx
            <Route path="/menu" element={<Menu />} />
            <Route path="/menu/inbox" element={<MenuInbox />} />
```

Crear placeholders temporales para que compile (se reemplazan en Tasks 13 y 15):

`frontend/src/pages/Menu.jsx`:

```jsx
const Menu = () => <div>Carta</div>
export default Menu
```

`frontend/src/pages/MenuInbox.jsx`:

```jsx
const MenuInbox = () => <div>Sin asignar</div>
export default MenuInbox
```

- [ ] **Step 5: Sidebar**

En `frontend/src/components/layout/Sidebar.jsx`, agregar `BookOpen` e `Inbox` al import de `lucide-react` (el segundo bloque, después de `LogIn,`):

```jsx
  LogIn,
  BookOpen,
  Inbox,
} from 'lucide-react'
```

y agregar un grupo al final de `navGroups` (después del grupo `analisis`):

```jsx
  {
    id: 'carta',
    label: 'Carta',
    icon: BookOpen,
    activeClass: 'text-rose-700 bg-rose-50 border-rose-200',
    headerClass: 'text-rose-700 bg-rose-50',
    items: [
      { to: '/menu', icon: BookOpen, label: 'Carta' },
      { to: '/menu/inbox', icon: Inbox, label: 'Sin asignar', subItem: true },
    ],
  },
```

- [ ] **Step 6: Verificar**

Run: `cd frontend && npm run build`
Expected: build sin errores.

Manual: con `npm run dev`, loguearse como admin → el sidebar muestra el grupo "Carta" con "Carta" y "Sin asignar"; ambos navegan a los placeholders.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/services/menuService.js frontend/src/utils/menuFormat.js frontend/src/components/menu/ModalShell.jsx frontend/src/App.jsx frontend/src/components/layout/Sidebar.jsx frontend/src/pages/Menu.jsx frontend/src/pages/MenuInbox.jsx
git commit -m "feat(menu-admin): add menu service, routes and sidebar group"
```

---

### Task 13: Pantalla "Carta" — lista, categorías, estado, sync y publicar

**Files:**
- Create: `frontend/src/components/menu/CategoryCard.jsx`
- Create: `frontend/src/components/menu/CategoryFormModal.jsx`
- Modify (reemplazar completo): `frontend/src/pages/Menu.jsx`

- [ ] **Step 1: Tarjeta de categoría**

`frontend/src/components/menu/CategoryCard.jsx`:

```jsx
import { useState } from 'react'
import { ChevronDown, ChevronRight, ChevronUp, Eye, EyeOff, Pencil, Plus, AlertTriangle, Link2, ImageOff } from 'lucide-react'
import { variantSummary } from '../../utils/menuFormat'

const IconButton = ({ onClick, label, disabled, children }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    aria-label={label}
    title={label}
    className="p-1.5 rounded text-gray-500 hover:text-gray-800 hover:bg-gray-100 disabled:opacity-30 disabled:hover:bg-transparent"
  >
    {children}
  </button>
)

const FudoBadge = ({ variants }) => {
  const linked = variants.filter((v) => v.fudo_product_id)
  if (linked.some((v) => v.fudo_status && v.fudo_status !== 'ok')) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded">
        <AlertTriangle className="h-3 w-3" /> Revisar Fudo
      </span>
    )
  }
  if (linked.length === 0) {
    return <span className="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">Precio manual</span>
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs text-green-700 bg-green-50 px-1.5 py-0.5 rounded">
      <Link2 className="h-3 w-3" /> Fudo
    </span>
  )
}

const ItemRow = ({ item, index, total, tagsById, onEdit, onToggle, onMove }) => (
  <li className={`flex items-center gap-3 py-2 px-3 ${item.is_visible ? '' : 'opacity-50'}`}>
    {item.image_url ? (
      <img src={item.image_url} alt="" className="h-12 w-12 rounded object-cover flex-shrink-0" />
    ) : (
      <div className="h-12 w-12 rounded bg-gray-100 flex items-center justify-center flex-shrink-0">
        <ImageOff className="h-4 w-4 text-gray-400" />
      </div>
    )}
    <button type="button" onClick={onEdit} className="flex-1 min-w-0 text-left">
      <div className="font-medium text-gray-900 truncate">
        {item.is_featured && <span className="text-amber-500 mr-1">★</span>}
        {item.name}
      </div>
      <div className="text-sm text-gray-600 truncate">{variantSummary(item.variants)}</div>
      <div className="flex flex-wrap gap-1 mt-1">
        <FudoBadge variants={item.variants} />
        {item.tag_ids.map((id) => tagsById[id] && (
          <span key={id} className="text-xs px-1.5 py-0.5 rounded text-white" style={{ backgroundColor: tagsById[id].color }}>
            {tagsById[id].name}
          </span>
        ))}
      </div>
    </button>
    <div className="flex items-center flex-shrink-0">
      <IconButton label="Subir" onClick={() => onMove(index, -1)} disabled={index === 0}><ChevronUp className="h-4 w-4" /></IconButton>
      <IconButton label="Bajar" onClick={() => onMove(index, 1)} disabled={index === total - 1}><ChevronDown className="h-4 w-4" /></IconButton>
      <IconButton label={item.is_visible ? 'Ocultar' : 'Mostrar'} onClick={onToggle}>
        {item.is_visible ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
      </IconButton>
    </div>
  </li>
)

const CategoryCard = ({ category, index, total, tagsById, onMove, onEdit, onToggle, onAddItem, onEditItem, onToggleItem, onMoveItem }) => {
  const [open, setOpen] = useState(true)

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${category.is_visible ? '' : 'opacity-60'}`}>
      <div className="flex items-center gap-2 p-3 border-b border-gray-100">
        <button type="button" onClick={() => setOpen(!open)} className="flex items-center gap-2 flex-1 min-w-0 text-left">
          {open ? <ChevronDown className="h-4 w-4 text-gray-500" /> : <ChevronRight className="h-4 w-4 text-gray-500" />}
          <span className="font-semibold text-gray-900 truncate">{category.name}</span>
          <span className="text-sm text-gray-500">({category.items.length})</span>
        </button>
        <IconButton label="Subir categoría" onClick={() => onMove(index, -1)} disabled={index === 0}><ChevronUp className="h-4 w-4" /></IconButton>
        <IconButton label="Bajar categoría" onClick={() => onMove(index, 1)} disabled={index === total - 1}><ChevronDown className="h-4 w-4" /></IconButton>
        <IconButton label={category.is_visible ? 'Ocultar categoría' : 'Mostrar categoría'} onClick={onToggle}>
          {category.is_visible ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
        </IconButton>
        <IconButton label="Editar categoría" onClick={onEdit}><Pencil className="h-4 w-4" /></IconButton>
        <button
          type="button"
          onClick={onAddItem}
          aria-label="Agregar ítem"
          className="inline-flex items-center gap-1 text-sm px-2 py-1 rounded bg-rose-50 text-rose-700 hover:bg-rose-100"
        >
          <Plus className="h-4 w-4" /> <span className="hidden sm:inline">Ítem</span>
        </button>
      </div>
      {open && (
        <ul className="divide-y divide-gray-100">
          {category.items.length === 0 && <li className="p-3 text-sm text-gray-500">Sin ítems todavía.</li>}
          {category.items.map((item, itemIndex) => (
            <ItemRow
              key={item.id}
              item={item}
              index={itemIndex}
              total={category.items.length}
              tagsById={tagsById}
              onEdit={() => onEditItem(item)}
              onToggle={() => onToggleItem(item)}
              onMove={(i, direction) => onMoveItem(category, i, direction)}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

export default CategoryCard
```

- [ ] **Step 2: Modal de categoría**

`frontend/src/components/menu/CategoryFormModal.jsx`:

```jsx
import { useState } from 'react'
import ModalShell from './ModalShell'
import menuService from '../../services/menuService'
import { errorMessage } from '../../utils/menuFormat'

const CategoryFormModal = ({ category, onClose, onSaved }) => {
  const [form, setForm] = useState({
    name: category?.name || '',
    description: category?.description || '',
    is_visible: category?.is_visible ?? true,
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (category) await menuService.updateCategory(category.id, form)
      else await menuService.createCategory(form)
      onSaved()
    } catch (err) {
      setError(errorMessage(err, 'Error al guardar la categoría'))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm(`¿Borrar la categoría "${category.name}"?`)) return
    setSaving(true)
    setError('')
    try {
      await menuService.deleteCategory(category.id)
      onSaved()
    } catch (err) {
      setError(errorMessage(err, 'Error al borrar la categoría'))
      setSaving(false)
    }
  }

  return (
    <ModalShell
      title={category ? 'Editar categoría' : 'Nueva categoría'}
      onClose={onClose}
      footer={
        <>
          {category && (
            <button type="button" onClick={handleDelete} disabled={saving} className="mr-auto px-4 py-2 text-red-600 hover:bg-red-50 rounded">
              Borrar
            </button>
          )}
          <button type="button" onClick={onClose} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">Cancelar</button>
          <button type="submit" form="category-form" disabled={saving} className="px-4 py-2 bg-rose-600 text-white rounded hover:bg-rose-700 disabled:opacity-50">
            {saving ? 'Guardando…' : 'Guardar'}
          </button>
        </>
      }
    >
      <form id="category-form" onSubmit={handleSubmit} className="space-y-4">
        {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-rose-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nota (se muestra bajo el título)</label>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={2}
            placeholder="Ej: Contanos si lo preferís con azúcar, stevia o sin nada"
            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-rose-500"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={form.is_visible} onChange={(e) => setForm({ ...form, is_visible: e.target.checked })} />
          Visible en la carta
        </label>
      </form>
    </ModalShell>
  )
}

export default CategoryFormModal
```

- [ ] **Step 3: Página principal**

Reemplazar `frontend/src/pages/Menu.jsx` completo:

```jsx
import { useState, useEffect, useCallback, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'
import { Plus, RefreshCw, Upload, ExternalLink, AlertTriangle, Inbox } from 'lucide-react'
import menuService from '../services/menuService'
import CategoryCard from '../components/menu/CategoryCard'
import CategoryFormModal from '../components/menu/CategoryFormModal'
import MenuItemModal from '../components/menu/MenuItemModal'
import MenuSettingsPanel from '../components/menu/MenuSettingsPanel'
import { swap, errorMessage, PUBLIC_MENU_URL } from '../utils/menuFormat'

const Menu = () => {
  const [menu, setMenu] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(null)
  const [tab, setTab] = useState('carta')
  const [categoryModal, setCategoryModal] = useState(null) // { category } | null
  const [itemModal, setItemModal] = useState(null) // { item, categoryId } | null

  const load = useCallback(async () => {
    try {
      setMenu(await menuService.getMenu())
      setError('')
    } catch (err) {
      setError(errorMessage(err, 'Error al cargar la carta'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const tagsById = useMemo(() => Object.fromEntries((menu?.tags || []).map((t) => [t.id, t])), [menu])

  const run = async (key, action, successMessage) => {
    setBusy(key)
    setError('')
    setNotice('')
    try {
      const result = await action()
      if (successMessage) setNotice(typeof successMessage === 'function' ? successMessage(result) : successMessage)
      await load()
    } catch (err) {
      setError(errorMessage(err, 'Ocurrió un error'))
    } finally {
      setBusy(null)
    }
  }

  const handleSync = () =>
    run('sync', menuService.syncFudo, (r) => `Fudo sincronizado: ${r.products} productos, ${r.price_changes} precios actualizados.`)

  const handlePublish = () => run('publish', menuService.publish, 'Carta publicada. Los clientes ya ven los cambios.')

  const moveCategory = (index, direction) => {
    const ids = swap(menu.categories.map((c) => c.id), index, index + direction)
    if (ids) run('reorder', () => menuService.reorderCategories(ids))
  }

  const moveItem = (category, index, direction) => {
    const ids = swap(category.items.map((i) => i.id), index, index + direction)
    if (ids) run('reorder', () => menuService.reorderItems(category.id, ids))
  }

  const closeModalsAndReload = () => {
    setCategoryModal(null)
    setItemModal(null)
    load()
  }

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-600" /></div>
  }

  const status = menu?.status
  const pendingCount = (status?.unassigned_count || 0) + (status?.alerts_count || 0)

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Carta</h1>
          <p className="text-sm text-gray-600">
            {status?.last_published_at
              ? `Última publicación: ${formatDistanceToNow(new Date(status.last_published_at), { addSuffix: true, locale: es })}`
              : 'Todavía no se publicó'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <a href={PUBLIC_MENU_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 px-3 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50">
            <ExternalLink className="h-4 w-4" /> Ver carta
          </a>
          <button type="button" onClick={handleSync} disabled={!!busy} className="inline-flex items-center gap-1 px-3 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50">
            <RefreshCw className={`h-4 w-4 ${busy === 'sync' ? 'animate-spin' : ''}`} /> Sincronizar Fudo
          </button>
          <button type="button" onClick={handlePublish} disabled={!!busy} className="inline-flex items-center gap-1 px-3 py-2 text-sm bg-rose-600 text-white rounded hover:bg-rose-700 disabled:opacity-50">
            <Upload className="h-4 w-4" /> {busy === 'publish' ? 'Publicando…' : 'Publicar'}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {status?.has_unpublished_changes && (
          <span className="inline-flex items-center gap-1 text-sm px-2 py-1 rounded bg-amber-50 text-amber-800">
            <span className="h-2 w-2 rounded-full bg-amber-500" /> Hay cambios sin publicar
          </span>
        )}
        {pendingCount > 0 && (
          <Link to="/menu/inbox" className="inline-flex items-center gap-1 text-sm px-2 py-1 rounded bg-blue-50 text-blue-800 hover:bg-blue-100">
            <Inbox className="h-4 w-4" /> {status.unassigned_count} sin asignar
            {status.alerts_count > 0 && <><AlertTriangle className="h-4 w-4 ml-1 text-amber-600" /> {status.alerts_count} alertas</>}
          </Link>
        )}
      </div>

      {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
      {notice && <div className="p-3 bg-green-50 text-green-700 rounded text-sm">{notice}</div>}

      <div className="flex gap-4 border-b border-gray-200">
        {[['carta', 'Carta'], ['config', 'Configuración']].map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`pb-2 text-sm font-medium border-b-2 ${tab === key ? 'border-rose-600 text-rose-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'carta' ? (
        <div className="space-y-3">
          {menu.categories.map((category, index) => (
            <CategoryCard
              key={category.id}
              category={category}
              index={index}
              total={menu.categories.length}
              tagsById={tagsById}
              onMove={moveCategory}
              onEdit={() => setCategoryModal({ category })}
              onToggle={() => run('toggle', () => menuService.updateCategory(category.id, { is_visible: !category.is_visible }))}
              onAddItem={() => setItemModal({ item: null, categoryId: category.id })}
              onEditItem={(item) => setItemModal({ item, categoryId: category.id })}
              onToggleItem={(item) => run('toggle', () => menuService.updateItem(item.id, { is_visible: !item.is_visible }))}
              onMoveItem={moveItem}
            />
          ))}
          <button
            type="button"
            onClick={() => setCategoryModal({ category: null })}
            className="w-full inline-flex items-center justify-center gap-1 py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-rose-400 hover:text-rose-700"
          >
            <Plus className="h-4 w-4" /> Categoría
          </button>
        </div>
      ) : (
        <MenuSettingsPanel tags={menu.tags} onChanged={load} />
      )}

      {categoryModal && (
        <CategoryFormModal category={categoryModal.category} onClose={() => setCategoryModal(null)} onSaved={closeModalsAndReload} />
      )}
      {itemModal && (
        <MenuItemModal
          item={itemModal.item}
          defaultCategoryId={itemModal.categoryId}
          categories={menu.categories}
          tags={menu.tags}
          onClose={() => setItemModal(null)}
          onSaved={closeModalsAndReload}
        />
      )}
    </div>
  )
}

export default Menu
```

> `MenuItemModal` y `MenuSettingsPanel` se crean en Task 14. Para que compile en este paso, crear stubs:
>
> `frontend/src/components/menu/MenuItemModal.jsx`: `const MenuItemModal = () => null` + `export default MenuItemModal`
> `frontend/src/components/menu/MenuSettingsPanel.jsx`: `const MenuSettingsPanel = () => null` + `export default MenuSettingsPanel`

- [ ] **Step 4: Verificar**

Run: `cd frontend && npm run build`
Expected: build sin errores.

Manual (con datos del seed de Task 11):
1. `/menu` lista las categorías con sus ítems y precios.
2. ↑↓ en una categoría cambia el orden y persiste al recargar.
3. El ojo oculta/muestra; el ítem/categoría se ve atenuado.
4. "+ Categoría" crea; el lápiz edita; borrar una categoría con ítems muestra el error "La categoría tiene ítems…".
5. "Publicar" muestra el mensaje de éxito y desaparece "Hay cambios sin publicar" (requiere AWS configurado — ver Task 21; si todavía no está, el error 502 se muestra en rojo y eso también es correcto).
6. En un viewport de 375px todo es usable sin scroll horizontal.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/menu/CategoryCard.jsx frontend/src/components/menu/CategoryFormModal.jsx frontend/src/components/menu/MenuItemModal.jsx frontend/src/components/menu/MenuSettingsPanel.jsx frontend/src/pages/Menu.jsx
git commit -m "feat(menu-admin): menu editor with categories, ordering, sync and publish"
```

---

### Task 14: Modal de ítem (variantes, Fudo, tags, foto) y configuración

**Files:**
- Create: `frontend/src/components/menu/FudoProductPicker.jsx`
- Modify (reemplazar stub): `frontend/src/components/menu/MenuItemModal.jsx`
- Modify (reemplazar stub): `frontend/src/components/menu/MenuSettingsPanel.jsx`

- [ ] **Step 1: Selector de producto de Fudo**

`frontend/src/components/menu/FudoProductPicker.jsx`:

```jsx
import { useState } from 'react'
import { normalizeText, formatPrice } from '../../utils/menuFormat'

// products: [{ fudo_id, name, price, category_name, linked }]
// allowedIds: ids que se pueden elegir aunque estén vinculados (los del propio ítem)
// excludedIds: ids ya usados en otras variantes de este formulario
const FudoProductPicker = ({ products, allowedIds, excludedIds, onSelect, onCancel }) => {
  const [query, setQuery] = useState('')
  const needle = normalizeText(query.trim())
  const visible = products
    .filter((p) => !needle || normalizeText(`${p.name} ${p.category_name || ''}`).includes(needle))
    .slice(0, 50)

  return (
    <div className="mt-2 border border-gray-200 rounded p-2 bg-gray-50">
      <input
        autoFocus
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Buscar producto en Fudo…"
        className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
      />
      <ul className="max-h-56 overflow-y-auto mt-2 divide-y divide-gray-200">
        {products.length === 0 && <li className="p-2 text-sm text-gray-500">No hay productos: tocá "Sincronizar Fudo" primero.</li>}
        {visible.map((p) => {
          const taken = (p.linked && !allowedIds.has(p.fudo_id)) || excludedIds.has(p.fudo_id)
          return (
            <li key={p.fudo_id}>
              <button
                type="button"
                disabled={taken}
                onClick={() => onSelect(p)}
                className="w-full text-left p-2 text-sm hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed flex justify-between gap-2"
              >
                <span>
                  {p.name}
                  {p.category_name && <span className="text-gray-500"> · {p.category_name}</span>}
                  {taken && <span className="text-gray-500"> · ya en la carta</span>}
                </span>
                <span className="text-gray-700">{formatPrice(p.price)}</span>
              </button>
            </li>
          )
        })}
      </ul>
      <button type="button" onClick={onCancel} className="mt-2 text-sm text-gray-600 hover:text-gray-900">Cancelar</button>
    </div>
  )
}

export default FudoProductPicker
```

- [ ] **Step 2: Modal de ítem**

Reemplazar `frontend/src/components/menu/MenuItemModal.jsx` completo:

```jsx
import { useState, useEffect, useMemo } from 'react'
import { Trash2, Plus, Link2, Unlink, ImagePlus } from 'lucide-react'
import ModalShell from './ModalShell'
import FudoProductPicker from './FudoProductPicker'
import menuService from '../../services/menuService'
import { formatPrice, errorMessage } from '../../utils/menuFormat'

const emptyVariant = () => ({ label: '', fudo_product_id: null, price: '' })

const toFormVariant = (v) => ({ label: v.label || '', fudo_product_id: v.fudo_product_id || null, price: v.price ?? '' })

// item: ítem existente o null. prefill: datos iniciales para un ítem nuevo (desde la bandeja).
const MenuItemModal = ({ item, prefill, categories, tags, defaultCategoryId, onClose, onSaved }) => {
  const source = item || prefill || {}
  const [form, setForm] = useState({
    name: source.name || '',
    description: source.description || '',
    category_id: source.category_id || defaultCategoryId || categories[0]?.id || '',
    is_visible: source.is_visible ?? true,
    is_featured: source.is_featured || false,
    tag_ids: source.tag_ids || [],
  })
  const [variants, setVariants] = useState(source.variants?.length ? source.variants.map(toFormVariant) : [emptyVariant()])
  const [products, setProducts] = useState([])
  const [pickerIndex, setPickerIndex] = useState(null)
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(item?.image_url || null)
  const [removeImage, setRemoveImage] = useState(false)
  const [savedItemId, setSavedItemId] = useState(item?.id || null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    menuService.getFudoProducts().then(setProducts).catch(() => setProducts([]))
  }, [])

  useEffect(() => () => {
    if (imagePreview?.startsWith('blob:')) URL.revokeObjectURL(imagePreview)
  }, [imagePreview])

  const productsById = useMemo(() => Object.fromEntries(products.map((p) => [p.fudo_id, p])), [products])
  const ownFudoIds = useMemo(() => new Set((item?.variants || []).map((v) => v.fudo_product_id).filter(Boolean)), [item])

  const updateVariant = (index, changes) => setVariants((vs) => vs.map((v, i) => (i === index ? { ...v, ...changes } : v)))
  const removeVariant = (index) => setVariants((vs) => vs.filter((_, i) => i !== index))

  const toggleTag = (id) =>
    setForm((f) => ({ ...f, tag_ids: f.tag_ids.includes(id) ? f.tag_ids.filter((t) => t !== id) : [...f.tag_ids, id] }))

  const handleImage = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setImageFile(file)
    setRemoveImage(false)
    setImagePreview(URL.createObjectURL(file))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    const payload = {
      ...form,
      category_id: Number(form.category_id),
      variants: variants.map((v) => ({
        label: v.label.trim() || null,
        fudo_product_id: v.fudo_product_id,
        price: v.fudo_product_id ? null : v.price,
      })),
    }
    try {
      const saved = savedItemId ? await menuService.updateItem(savedItemId, payload) : await menuService.createItem(payload)
      setSavedItemId(saved.id)
      if (imageFile) await menuService.uploadItemImage(saved.id, imageFile)
      else if (removeImage && saved.image_key) await menuService.deleteItemImage(saved.id)
      onSaved()
    } catch (err) {
      setError(errorMessage(err, 'Error al guardar el ítem'))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm(`¿Borrar "${item.name}" de la carta?`)) return
    setSaving(true)
    try {
      await menuService.deleteItem(item.id)
      onSaved()
    } catch (err) {
      setError(errorMessage(err, 'Error al borrar el ítem'))
      setSaving(false)
    }
  }

  const usedFudoIds = (exceptIndex) =>
    new Set(variants.filter((v, i) => i !== exceptIndex && v.fudo_product_id).map((v) => v.fudo_product_id))

  return (
    <ModalShell
      title={item ? 'Editar ítem' : 'Nuevo ítem'}
      onClose={onClose}
      footer={
        <>
          {item && (
            <button type="button" onClick={handleDelete} disabled={saving} className="mr-auto px-4 py-2 text-red-600 hover:bg-red-50 rounded">
              Borrar
            </button>
          )}
          <button type="button" onClick={onClose} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">Cancelar</button>
          <button type="submit" form="item-form" disabled={saving} className="px-4 py-2 bg-rose-600 text-white rounded hover:bg-rose-700 disabled:opacity-50">
            {saving ? 'Guardando…' : 'Guardar'}
          </button>
        </>
      }
    >
      <form id="item-form" onSubmit={handleSubmit} className="space-y-4">
        {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required className="w-full px-3 py-2 border border-gray-300 rounded" />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
          <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className="w-full px-3 py-2 border border-gray-300 rounded" />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Categoría</label>
          <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded">
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        <div>
          <span className="block text-sm font-medium text-gray-700 mb-1">Foto</span>
          <div className="flex items-center gap-3">
            {imagePreview && !removeImage ? (
              <img src={imagePreview} alt="" className="h-20 w-20 rounded object-cover" />
            ) : (
              <div className="h-20 w-20 rounded bg-gray-100" />
            )}
            <label className="inline-flex items-center gap-1 px-3 py-2 text-sm border border-gray-300 rounded cursor-pointer hover:bg-gray-50">
              <ImagePlus className="h-4 w-4" /> {imagePreview && !removeImage ? 'Cambiar' : 'Subir'}
              <input type="file" accept="image/jpeg,image/png,image/webp" onChange={handleImage} className="hidden" />
            </label>
            {imagePreview && !removeImage && (
              <button type="button" onClick={() => { setRemoveImage(true); setImageFile(null) }} className="text-sm text-red-600 hover:underline">
                Quitar
              </button>
            )}
          </div>
        </div>

        <div>
          <span className="block text-sm font-medium text-gray-700 mb-1">Precios *</span>
          <div className="space-y-2">
            {variants.map((variant, index) => {
              const product = variant.fudo_product_id ? productsById[variant.fudo_product_id] : null
              return (
                <div key={index} className="border border-gray-200 rounded p-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      value={variant.label}
                      onChange={(e) => updateVariant(index, { label: e.target.value })}
                      placeholder={variants.length > 1 ? 'Etiqueta (ej: Porción)' : 'Etiqueta (opcional)'}
                      className="flex-1 min-w-[8rem] px-2 py-1.5 border border-gray-300 rounded text-sm"
                    />
                    {variant.fudo_product_id ? (
                      <span className="text-sm text-gray-800 px-2" title="Precio tomado de Fudo">
                        {formatPrice(product?.price ?? variant.price)} <span className="text-xs text-gray-500">de Fudo</span>
                      </span>
                    ) : (
                      <input
                        type="number"
                        min="0"
                        step="any"
                        value={variant.price}
                        onChange={(e) => updateVariant(index, { price: e.target.value })}
                        placeholder="Precio"
                        required
                        className="w-28 px-2 py-1.5 border border-gray-300 rounded text-sm"
                      />
                    )}
                    {variants.length > 1 && (
                      <button type="button" onClick={() => removeVariant(index)} className="p-1 text-gray-500 hover:text-red-600" aria-label="Quitar precio">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                  <div className="mt-1 text-xs">
                    {variant.fudo_product_id ? (
                      <button type="button" onClick={() => updateVariant(index, { fudo_product_id: null, price: product?.price ?? variant.price })} className="inline-flex items-center gap-1 text-gray-600 hover:text-gray-900">
                        <Unlink className="h-3 w-3" /> Vinculado a "{product?.name || variant.fudo_product_id}" — desvincular
                      </button>
                    ) : (
                      <button type="button" onClick={() => setPickerIndex(index)} className="inline-flex items-center gap-1 text-rose-700 hover:underline">
                        <Link2 className="h-3 w-3" /> Vincular con Fudo
                      </button>
                    )}
                  </div>
                  {pickerIndex === index && (
                    <FudoProductPicker
                      products={products}
                      allowedIds={ownFudoIds}
                      excludedIds={usedFudoIds(index)}
                      onCancel={() => setPickerIndex(null)}
                      onSelect={(p) => {
                        updateVariant(index, { fudo_product_id: p.fudo_id, price: p.price })
                        setPickerIndex(null)
                      }}
                    />
                  )}
                </div>
              )
            })}
          </div>
          <button type="button" onClick={() => setVariants([...variants, emptyVariant()])} className="mt-2 inline-flex items-center gap-1 text-sm text-rose-700 hover:underline">
            <Plus className="h-4 w-4" /> Agregar otro precio
          </button>
        </div>

        {tags.length > 0 && (
          <div>
            <span className="block text-sm font-medium text-gray-700 mb-1">Etiquetas</span>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => {
                const active = form.tag_ids.includes(tag.id)
                return (
                  <button
                    key={tag.id}
                    type="button"
                    onClick={() => toggleTag(tag.id)}
                    className={`text-sm px-2 py-1 rounded border ${active ? 'text-white' : 'text-gray-700 bg-white'}`}
                    style={active ? { backgroundColor: tag.color, borderColor: tag.color } : { borderColor: tag.color }}
                  >
                    {tag.name}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        <div className="flex flex-wrap gap-4">
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={form.is_featured} onChange={(e) => setForm({ ...form, is_featured: e.target.checked })} />
            Destacado ★
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={form.is_visible} onChange={(e) => setForm({ ...form, is_visible: e.target.checked })} />
            Visible en la carta
          </label>
        </div>
      </form>
    </ModalShell>
  )
}

export default MenuItemModal
```

- [ ] **Step 3: Panel de configuración**

Reemplazar `frontend/src/components/menu/MenuSettingsPanel.jsx` completo:

```jsx
import { useState, useEffect } from 'react'
import { Plus, Trash2, Save } from 'lucide-react'
import menuService from '../../services/menuService'
import { errorMessage } from '../../utils/menuFormat'

const TagRow = ({ tag, onChanged, onError }) => {
  const [name, setName] = useState(tag.name)
  const [color, setColor] = useState(tag.color)
  const dirty = name !== tag.name || color !== tag.color

  const save = async () => {
    try {
      await menuService.updateTag(tag.id, { name, color })
      onChanged()
    } catch (err) {
      onError(errorMessage(err, 'Error al guardar la etiqueta'))
    }
  }

  const remove = async () => {
    if (!window.confirm(`¿Borrar la etiqueta "${tag.name}"? Se quita de todos los ítems.`)) return
    try {
      await menuService.deleteTag(tag.id)
      onChanged()
    } catch (err) {
      onError(errorMessage(err, 'Error al borrar la etiqueta'))
    }
  }

  return (
    <li className="flex items-center gap-2 py-2">
      <input type="color" value={color} onChange={(e) => setColor(e.target.value)} className="h-8 w-10 border border-gray-300 rounded" />
      <input value={name} onChange={(e) => setName(e.target.value)} className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm" />
      {dirty && (
        <button type="button" onClick={save} className="p-1.5 text-rose-700 hover:bg-rose-50 rounded" aria-label="Guardar etiqueta">
          <Save className="h-4 w-4" />
        </button>
      )}
      <button type="button" onClick={remove} className="p-1.5 text-gray-500 hover:text-red-600 rounded" aria-label="Borrar etiqueta">
        <Trash2 className="h-4 w-4" />
      </button>
    </li>
  )
}

const MenuSettingsPanel = ({ tags, onChanged }) => {
  const [settings, setSettings] = useState({ footer_text: '', instagram: '' })
  const [newTag, setNewTag] = useState({ name: '', color: '#5C2E46' })
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    menuService.getSettings().then(setSettings).catch((err) => setError(errorMessage(err, 'Error al cargar la configuración')))
  }, [])

  const saveSettings = async (e) => {
    e.preventDefault()
    setError('')
    try {
      setSettings(await menuService.updateSettings(settings))
      setNotice('Configuración guardada. Publicá la carta para que se vea.')
      onChanged()
    } catch (err) {
      setError(errorMessage(err, 'Error al guardar la configuración'))
    }
  }

  const addTag = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await menuService.createTag(newTag)
      setNewTag({ name: '', color: '#5C2E46' })
      onChanged()
    } catch (err) {
      setError(errorMessage(err, 'Error al crear la etiqueta'))
    }
  }

  return (
    <div className="space-y-6">
      {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
      {notice && <div className="p-3 bg-green-50 text-green-700 rounded text-sm">{notice}</div>}

      <section className="bg-white rounded-lg border border-gray-200 p-4">
        <h2 className="font-semibold text-gray-900 mb-2">Etiquetas</h2>
        <ul className="divide-y divide-gray-100">
          {tags.map((tag) => <TagRow key={`${tag.id}-${tag.name}-${tag.color}`} tag={tag} onChanged={onChanged} onError={setError} />)}
        </ul>
        <form onSubmit={addTag} className="flex items-center gap-2 mt-3">
          <input type="color" value={newTag.color} onChange={(e) => setNewTag({ ...newTag, color: e.target.value })} className="h-8 w-10 border border-gray-300 rounded" />
          <input value={newTag.name} onChange={(e) => setNewTag({ ...newTag, name: e.target.value })} placeholder="Nueva etiqueta (ej: Sin TACC)" required className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm" />
          <button type="submit" className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-rose-600 text-white rounded hover:bg-rose-700">
            <Plus className="h-4 w-4" /> Agregar
          </button>
        </form>
      </section>

      <form onSubmit={saveSettings} className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <h2 className="font-semibold text-gray-900">Textos de la carta</h2>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Mensaje al pie</label>
          <textarea value={settings.footer_text} onChange={(e) => setSettings({ ...settings, footer_text: e.target.value })} rows={4} className="w-full px-3 py-2 border border-gray-300 rounded" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Instagram</label>
          <input value={settings.instagram} onChange={(e) => setSettings({ ...settings, instagram: e.target.value })} placeholder="@galia" className="w-full px-3 py-2 border border-gray-300 rounded" />
        </div>
        <button type="submit" className="px-4 py-2 bg-rose-600 text-white rounded hover:bg-rose-700">Guardar textos</button>
      </form>
    </div>
  )
}

export default MenuSettingsPanel
```

- [ ] **Step 4: Verificar**

Run: `cd frontend && npm run build`
Expected: build sin errores.

Manual (con `POST /api/v1/menu/sync` hecho al menos una vez, o con productos en `fudo_products`):
1. Crear ítem con precio manual → aparece con badge "Precio manual".
2. Editar → "Vincular con Fudo" → buscar sin tildes ("cafe") → elegir → el precio pasa a solo lectura "de Fudo"; guardar → badge "Fudo".
3. Productos ya usados en otro ítem aparecen deshabilitados con "ya en la carta".
4. "Agregar otro precio" con etiquetas Porción/Entera → la fila muestra `Porción $X · Entera $Y`.
5. Subir foto JPG desde el celular (o devtools mobile) → miniatura en la lista. "Quitar" + guardar → sin foto.
6. Tags: crear "Sin TACC" en Configuración, asignarlo a un ítem, verlo en la fila; cambiar color y guardar.
7. Textos: guardar mensaje al pie → aparece "Hay cambios sin publicar".

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/menu/FudoProductPicker.jsx frontend/src/components/menu/MenuItemModal.jsx frontend/src/components/menu/MenuSettingsPanel.jsx
git commit -m "feat(menu-admin): item editor with Fudo linking, photos, tags and settings"
```

---

### Task 15: Bandeja "Sin asignar" y alertas

**Files:**
- Modify (reemplazar placeholder): `frontend/src/pages/MenuInbox.jsx`

- [ ] **Step 1: Write the page**

Reemplazar `frontend/src/pages/MenuInbox.jsx` completo:

```jsx
import { useState, useEffect, useCallback, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Plus, EyeOff, AlertTriangle, Link2 } from 'lucide-react'
import menuService from '../services/menuService'
import MenuItemModal from '../components/menu/MenuItemModal'
import { formatPrice, errorMessage } from '../utils/menuFormat'

const STATUS_TEXT = {
  inactive: 'El producto está desactivado en Fudo',
  missing: 'El producto ya no existe en Fudo',
}

const MenuInbox = () => {
  const [inbox, setInbox] = useState({ unassigned: [], alerts: [] })
  const [menu, setMenu] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modal, setModal] = useState(null) // { item } | { prefill }
  const [attaching, setAttaching] = useState(null) // fudo_id que se está agregando a un ítem existente
  const [targetItemId, setTargetItemId] = useState('')

  const load = useCallback(async () => {
    try {
      const [inboxData, menuData] = await Promise.all([menuService.getInbox(), menuService.getMenu()])
      setInbox(inboxData)
      setMenu(menuData)
      setError('')
    } catch (err) {
      setError(errorMessage(err, 'Error al cargar la bandeja'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const allItems = useMemo(
    () => (menu?.categories || []).flatMap((c) => c.items.map((i) => ({ ...i, categoryName: c.name }))),
    [menu],
  )
  const itemsById = useMemo(() => Object.fromEntries(allItems.map((i) => [i.id, i])), [allItems])

  const ignore = async (product) => {
    try {
      await menuService.ignoreFudoProduct(product.fudo_id)
      load()
    } catch (err) {
      setError(errorMessage(err, 'Error al ignorar el producto'))
    }
  }

  const attachToItem = async (product) => {
    const item = itemsById[Number(targetItemId)]
    if (!item) return
    const variants = [
      ...item.variants.map((v) => ({ label: v.label, fudo_product_id: v.fudo_product_id, price: v.price })),
      { label: product.name, fudo_product_id: product.fudo_id, price: null },
    ]
    try {
      await menuService.updateItem(item.id, { variants })
      setAttaching(null)
      setTargetItemId('')
      load()
    } catch (err) {
      setError(errorMessage(err, 'Error al agregar el precio al ítem'))
    }
  }

  const closeAndReload = () => {
    setModal(null)
    load()
  }

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-600" /></div>
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/menu" className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900">
          <ArrowLeft className="h-4 w-4" /> Volver a la carta
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mt-1">Sin asignar y alertas</h1>
      </div>

      {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      <section className="bg-white rounded-lg border border-gray-200">
        <h2 className="font-semibold text-gray-900 p-4 border-b border-gray-100 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-600" /> Alertas ({inbox.alerts.length})
        </h2>
        <ul className="divide-y divide-gray-100">
          {inbox.alerts.length === 0 && <li className="p-4 text-sm text-gray-500">Sin alertas.</li>}
          {inbox.alerts.map((alert) => (
            <li key={alert.id} className="p-4 flex flex-col sm:flex-row sm:items-center gap-2">
              <div className="flex-1">
                <div className="font-medium text-gray-900">
                  {alert.item_name}{alert.label && <span className="text-gray-500"> · {alert.label}</span>}
                </div>
                <div className="text-sm text-amber-700">{STATUS_TEXT[alert.fudo_status]}{alert.fudo_name && ` ("${alert.fudo_name}")`}</div>
              </div>
              <button type="button" onClick={() => setModal({ item: itemsById[alert.item_id] })} className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50">
                Editar ítem
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="bg-white rounded-lg border border-gray-200">
        <h2 className="font-semibold text-gray-900 p-4 border-b border-gray-100">
          Productos de Fudo sin asignar ({inbox.unassigned.length})
        </h2>
        <ul className="divide-y divide-gray-100">
          {inbox.unassigned.length === 0 && <li className="p-4 text-sm text-gray-500">Todos los productos de Fudo están en la carta o ignorados.</li>}
          {inbox.unassigned.map((product) => (
            <li key={product.fudo_id} className="p-4 space-y-2">
              <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{product.name}</div>
                  <div className="text-sm text-gray-600">{product.category_name || 'Sin categoría'} · {formatPrice(product.price)}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => setModal({ prefill: { name: product.name, variants: [{ label: null, fudo_product_id: product.fudo_id, price: product.price }] } })}
                    className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-rose-600 text-white rounded hover:bg-rose-700"
                  >
                    <Plus className="h-4 w-4" /> Crear ítem
                  </button>
                  <button
                    type="button"
                    onClick={() => { setAttaching(product.fudo_id); setTargetItemId('') }}
                    className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50"
                  >
                    <Link2 className="h-4 w-4" /> Agregar a un ítem
                  </button>
                  <button type="button" onClick={() => ignore(product)} className="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 rounded hover:bg-gray-100">
                    <EyeOff className="h-4 w-4" /> Ignorar
                  </button>
                </div>
              </div>
              {attaching === product.fudo_id && (
                <div className="flex flex-col sm:flex-row gap-2">
                  <select value={targetItemId} onChange={(e) => setTargetItemId(e.target.value)} className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm">
                    <option value="">Elegí el ítem…</option>
                    {allItems.map((i) => <option key={i.id} value={i.id}>{i.categoryName} · {i.name}</option>)}
                  </select>
                  <button type="button" disabled={!targetItemId} onClick={() => attachToItem(product)} className="px-3 py-2 text-sm bg-rose-600 text-white rounded disabled:opacity-50">
                    Agregar como precio
                  </button>
                  <button type="button" onClick={() => setAttaching(null)} className="px-3 py-2 text-sm text-gray-600">Cancelar</button>
                </div>
              )}
            </li>
          ))}
        </ul>
      </section>

      {modal && menu && (
        <MenuItemModal
          item={modal.item || null}
          prefill={modal.prefill}
          defaultCategoryId={modal.item?.category_id}
          categories={menu.categories}
          tags={menu.tags}
          onClose={() => setModal(null)}
          onSaved={closeAndReload}
        />
      )}
    </div>
  )
}

export default MenuInbox
```

> Nota: "Agregar a un ítem" usa el nombre del producto como etiqueta de la nueva variante; la encargada puede editarla después en el modal (ej. "Entera").

- [ ] **Step 2: Verificar**

Run: `cd frontend && npm run build`
Expected: build sin errores.

Manual (tras sincronizar Fudo con la carta del seed sin vincular):
1. `/menu/inbox` lista los productos de Fudo con categoría y precio.
2. "Crear ítem" abre el modal con nombre y variante vinculada; al guardar el producto desaparece de la bandeja.
3. "Agregar a un ítem" → elegir "Tortas · Torta Galia" → el ítem queda con un precio extra vinculado.
4. "Ignorar" lo saca de la lista y no vuelve tras otra sincronización.
5. Desactivar (o simular con SQL `UPDATE fudo_products SET is_active=false WHERE fudo_id='X'` y re-sync real) → aparece en Alertas; "Editar ítem" abre el modal correcto.
6. El contador del link en `/menu` coincide con la bandeja.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/MenuInbox.jsx
git commit -m "feat(menu-admin): inbox for unassigned Fudo products and alerts"
```

---

## Phase C — Carta pública (`menu-site/`)

### Task 16: Scaffold del sitio

**Files:**
- Create: `menu-site/package.json`, `menu-site/vite.config.js`, `menu-site/tailwind.config.js`, `menu-site/postcss.config.js`, `menu-site/index.html`, `menu-site/.gitignore`, `menu-site/.env.example`, `menu-site/src/main.jsx`, `menu-site/src/index.css`, `menu-site/src/App.jsx` (placeholder)

- [ ] **Step 1: Archivos de configuración**

`menu-site/package.json`:

```json
{
  "name": "galia-carta",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.4.0",
    "vite": "^5.0.8",
    "vitest": "^1.6.0"
  }
}
```

`menu-site/vite.config.js`:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 5174 },
  test: { environment: 'node' },
})
```

`menu-site/tailwind.config.js`:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        cream: '#F5F1EA',
        plum: { DEFAULT: '#5C2E46', dark: '#43203A', light: '#8A5A72' },
        lime: '#C5D94A',
        coral: '#E0866A',
      },
      fontFamily: {
        display: ['Anton', 'Impact', 'sans-serif'],
        body: ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```

`menu-site/postcss.config.js`:

```js
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}
```

`menu-site/.gitignore`:

```
node_modules
dist
.env.local
```

`menu-site/.env.example`:

```
# URL pública del menu.json (prefijo menu/ del bucket S3)
VITE_MENU_URL=https://<bucket>.s3.<region>.amazonaws.com/menu/menu.json
```

`menu-site/index.html`:

```html
<!doctype html>
<html lang="es-AR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#F5F1EA" />
    <meta name="description" content="Carta de Galia" />
    <link rel="icon" type="image/png" href="/brand/favicon.png" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Anton&family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet" />
    <title>Galia · Carta</title>
  </head>
  <body class="bg-cream">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

`menu-site/src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html {
  scroll-behavior: smooth;
}

body {
  @apply bg-cream text-plum font-body antialiased;
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}

.no-scrollbar {
  scrollbar-width: none;
}
```

`menu-site/src/main.jsx`:

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

`menu-site/src/App.jsx` (placeholder, se reemplaza en Task 19):

```jsx
export default function App() {
  return <h1 className="font-display text-5xl text-plum text-center p-8">GALIA</h1>
}
```

- [ ] **Step 2: Instalar y levantar**

Run: `cd menu-site && npm install && npm run build`
Expected: build OK, genera `menu-site/dist/`.

Run: `cd menu-site && npm run dev` → abrir `http://localhost:5174`.
Expected: "GALIA" en tipografía Anton, bordó sobre crema.

- [ ] **Step 3: Commit**

```bash
git add menu-site/package.json menu-site/package-lock.json menu-site/vite.config.js menu-site/tailwind.config.js menu-site/postcss.config.js menu-site/index.html menu-site/.gitignore menu-site/.env.example menu-site/src
git commit -m "feat(menu-site): scaffold public menu site with brand theme"
```

---

### Task 17: Lógica pura — texto, precios y filtros

**Files:**
- Create: `menu-site/src/lib/text.js`, `menu-site/src/lib/format.js`, `menu-site/src/lib/filterMenu.js`
- Test: `menu-site/src/lib/text.test.js`, `menu-site/src/lib/format.test.js`, `menu-site/src/lib/filterMenu.test.js`

- [ ] **Step 1: Write the failing tests**

`menu-site/src/lib/text.test.js`:

```js
import { describe, it, expect } from 'vitest'
import { normalize } from './text'

describe('normalize', () => {
  it('quita tildes y pasa a minúsculas', () => {
    expect(normalize('Café con LECHE Ñandú')).toBe('cafe con leche nandu')
  })

  it('tolera null', () => {
    expect(normalize(null)).toBe('')
  })
})
```

`menu-site/src/lib/format.test.js`:

```js
import { describe, it, expect } from 'vitest'
import { formatPrice, formatVariant } from './format'

describe('formatPrice', () => {
  it('usa separador de miles argentino', () => {
    expect(formatPrice(6900)).toBe('$6.900')
    expect(formatPrice(12600.5)).toBe('$12.600,5')
  })
})

describe('formatVariant', () => {
  it('incluye la etiqueta si existe', () => {
    expect(formatVariant({ label: 'Porción', price: 11200 })).toBe('Porción $11.200')
    expect(formatVariant({ label: null, price: 4400 })).toBe('$4.400')
  })
})
```

`menu-site/src/lib/filterMenu.test.js`:

```js
import { describe, it, expect } from 'vitest'
import { filterMenu } from './filterMenu'

const categories = [
  {
    slug: 'cafes',
    name: 'Cafés',
    items: [
      { id: 1, name: 'Café con leche', description: null, tags: [] },
      { id: 2, name: 'Latte', description: 'Con leche de almendras', tags: ['vegano'] },
    ],
  },
  {
    slug: 'tortas',
    name: 'Tortas',
    items: [{ id: 3, name: 'Torta Galia', description: 'Masa de nuez', tags: ['sin-tacc', 'vegano'] }],
  },
]

describe('filterMenu', () => {
  it('sin filtros devuelve todo', () => {
    expect(filterMenu(categories)).toEqual(categories)
  })

  it('busca sin tildes en nombre y descripción y oculta categorías vacías', () => {
    const result = filterMenu(categories, { query: 'CAFE' })
    expect(result.map((c) => c.slug)).toEqual(['cafes'])
    expect(result[0].items.map((i) => i.id)).toEqual([1])

    expect(filterMenu(categories, { query: 'almendras' })[0].items.map((i) => i.id)).toEqual([2])
  })

  it('combina etiquetas con Y', () => {
    expect(filterMenu(categories, { tagSlugs: ['vegano'] }).flatMap((c) => c.items.map((i) => i.id))).toEqual([2, 3])
    expect(filterMenu(categories, { tagSlugs: ['vegano', 'sin-tacc'] }).flatMap((c) => c.items.map((i) => i.id))).toEqual([3])
  })

  it('combina búsqueda y etiquetas', () => {
    expect(filterMenu(categories, { query: 'latte', tagSlugs: ['sin-tacc'] })).toEqual([])
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd menu-site && npm test`
Expected: FAIL — `Failed to resolve import "./text"` (y equivalentes).

- [ ] **Step 3: Write implementation**

`menu-site/src/lib/text.js`:

```js
export function normalize(text) {
  return (text || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}
```

`menu-site/src/lib/format.js`:

```js
const numberFormat = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 2 })

export function formatPrice(price) {
  return `$${numberFormat.format(price)}`
}

export function formatVariant(variant) {
  return variant.label ? `${variant.label} ${formatPrice(variant.price)}` : formatPrice(variant.price)
}
```

`menu-site/src/lib/filterMenu.js`:

```js
import { normalize } from './text'

function matchesQuery(item, needle) {
  if (!needle) return true
  return normalize(`${item.name} ${item.description || ''}`).includes(needle)
}

export function filterMenu(categories, { query = '', tagSlugs = [] } = {}) {
  const needle = normalize(query).trim()
  if (!needle && tagSlugs.length === 0) return categories
  return categories
    .map((category) => ({
      ...category,
      items: category.items.filter(
        (item) => matchesQuery(item, needle) && tagSlugs.every((slug) => item.tags.includes(slug)),
      ),
    }))
    .filter((category) => category.items.length > 0)
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd menu-site && npm test`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add menu-site/src/lib
git commit -m "feat(menu-site): text normalization, price formatting and menu filtering"
```

---

### Task 18: Carga de `menu.json` con respaldo en caché

**Files:**
- Create: `menu-site/src/lib/loadMenu.js`
- Test: `menu-site/src/lib/loadMenu.test.js`

- [ ] **Step 1: Write the failing test**

`menu-site/src/lib/loadMenu.test.js`:

```js
import { describe, it, expect } from 'vitest'
import { loadMenu, CACHE_KEY, MenuUnavailableError } from './loadMenu'

const validMenu = { version: 1, settings: {}, tags: [], categories: [{ slug: 'cafes', name: 'Cafés', items: [] }] }

function memoryStorage(initial = {}) {
  const data = { ...initial }
  return {
    getItem: (key) => (key in data ? data[key] : null),
    setItem: (key, value) => { data[key] = value },
    data,
  }
}

const okFetch = (body) => async () => ({ ok: true, status: 200, json: async () => body })
const failingFetch = async () => { throw new Error('offline') }

describe('loadMenu', () => {
  it('descarga y cachea la carta', async () => {
    const storage = memoryStorage()
    const result = await loadMenu({ url: 'u', fetchImpl: okFetch(validMenu), storage })
    expect(result).toEqual({ menu: validMenu, source: 'network' })
    expect(JSON.parse(storage.data[CACHE_KEY])).toEqual(validMenu)
  })

  it('usa la caché si la red falla', async () => {
    const storage = memoryStorage({ [CACHE_KEY]: JSON.stringify(validMenu) })
    const result = await loadMenu({ url: 'u', fetchImpl: failingFetch, storage })
    expect(result).toEqual({ menu: validMenu, source: 'cache' })
  })

  it('usa la caché si la respuesta es inválida', async () => {
    const storage = memoryStorage({ [CACHE_KEY]: JSON.stringify(validMenu) })
    const result = await loadMenu({ url: 'u', fetchImpl: okFetch({ version: 99 }), storage })
    expect(result.source).toBe('cache')
  })

  it('usa la caché ante un HTTP de error', async () => {
    const storage = memoryStorage({ [CACHE_KEY]: JSON.stringify(validMenu) })
    const notFound = async () => ({ ok: false, status: 404, json: async () => ({}) })
    expect((await loadMenu({ url: 'u', fetchImpl: notFound, storage })).source).toBe('cache')
  })

  it('falla si no hay red ni caché válida', async () => {
    const storage = memoryStorage({ [CACHE_KEY]: '{roto' })
    await expect(loadMenu({ url: 'u', fetchImpl: failingFetch, storage })).rejects.toBeInstanceOf(MenuUnavailableError)
  })

  it('funciona sin storage disponible', async () => {
    const result = await loadMenu({ url: 'u', fetchImpl: okFetch(validMenu), storage: null })
    expect(result.source).toBe('network')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd menu-site && npm test -- loadMenu`
Expected: FAIL — `Failed to resolve import "./loadMenu"`

- [ ] **Step 3: Write implementation**

`menu-site/src/lib/loadMenu.js`:

```js
export const CACHE_KEY = 'galia-menu-v1'

export class MenuUnavailableError extends Error {}

function isValidMenu(data) {
  return Boolean(data) && data.version === 1 && Array.isArray(data.categories)
}

export function browserStorage() {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

function readCache(storage) {
  try {
    return JSON.parse(storage?.getItem(CACHE_KEY) || 'null')
  } catch {
    return null
  }
}

export async function loadMenu({ url, fetchImpl = globalThis.fetch, storage = browserStorage() } = {}) {
  try {
    const response = await fetchImpl(url, { cache: 'no-cache' })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const menu = await response.json()
    if (!isValidMenu(menu)) throw new Error('Formato de carta inválido')
    try {
      storage?.setItem(CACHE_KEY, JSON.stringify(menu))
    } catch {
      // storage lleno o bloqueado: la carta igual se muestra
    }
    return { menu, source: 'network' }
  } catch (error) {
    const cached = readCache(storage)
    if (isValidMenu(cached)) return { menu: cached, source: 'cache' }
    throw new MenuUnavailableError(error.message)
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd menu-site && npm test`
Expected: 14 passed

- [ ] **Step 5: Commit**

```bash
git add menu-site/src/lib/loadMenu.js menu-site/src/lib/loadMenu.test.js
git commit -m "feat(menu-site): load menu.json with localStorage fallback"
```

---

### Task 19: Interfaz de la carta

**Files:**
- Create: `menu-site/src/components/Header.jsx`, `SearchBar.jsx`, `TagFilters.jsx`, `CategoryNav.jsx`, `CategorySection.jsx`, `MenuItem.jsx`, `Lightbox.jsx`, `Footer.jsx`, `MenuMessage.jsx`
- Modify (reemplazar): `menu-site/src/App.jsx`
- Create: `menu-site/public/menu.sample.json` (datos para desarrollo local)

- [ ] **Step 1: Componentes**

`menu-site/src/components/Header.jsx`:

```jsx
export default function Header() {
  return (
    <header className="relative overflow-hidden pt-8 pb-4 text-center">
      <img src="/brand/flower-lime.png" alt="" aria-hidden="true" className="absolute -left-6 -top-4 w-24 rotate-12 opacity-90" />
      <img src="/brand/flower-coral.png" alt="" aria-hidden="true" className="absolute -right-5 top-6 w-20 -rotate-12 opacity-90" />
      <img src="/brand/logo.png" alt="Galia" className="mx-auto h-28 w-auto" />
    </header>
  )
}
```

`menu-site/src/components/SearchBar.jsx`:

```jsx
export default function SearchBar({ value, onChange }) {
  return (
    <label className="relative block">
      <span className="sr-only">Buscar en la carta</span>
      <svg aria-hidden="true" viewBox="0 0 20 20" className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 fill-plum-light">
        <path d="M8.5 3a5.5 5.5 0 014.38 8.83l3.65 3.64-1.06 1.06-3.64-3.65A5.5 5.5 0 118.5 3zm0 1.5a4 4 0 100 8 4 4 0 000-8z" />
      </svg>
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Buscar… (ej: frutilla)"
        className="w-full rounded-full border border-plum/20 bg-white py-2.5 pl-9 pr-4 text-base text-plum placeholder:text-plum-light focus:outline-none focus:ring-2 focus:ring-coral"
      />
    </label>
  )
}
```

`menu-site/src/components/TagFilters.jsx`:

```jsx
export default function TagFilters({ tags, active, onToggle }) {
  if (tags.length === 0) return null
  return (
    <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
      {tags.map((tag) => {
        const isActive = active.includes(tag.slug)
        return (
          <button
            key={tag.slug}
            type="button"
            aria-pressed={isActive}
            onClick={() => onToggle(tag.slug)}
            className="whitespace-nowrap rounded-full border px-3 py-1 text-sm font-medium transition-colors"
            style={isActive ? { backgroundColor: tag.color, borderColor: tag.color, color: '#fff' } : { borderColor: tag.color, color: tag.color }}
          >
            {tag.name}
          </button>
        )
      })}
    </div>
  )
}
```

`menu-site/src/components/CategoryNav.jsx`:

```jsx
import { useEffect, useRef, useState } from 'react'

export const sectionId = (slug) => `cat-${slug}`

export default function CategoryNav({ categories }) {
  const [activeSlug, setActiveSlug] = useState(categories[0]?.slug)
  const chipRefs = useRef({})

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting)
        if (visible.length > 0) setActiveSlug(visible[0].target.dataset.slug)
      },
      { rootMargin: '-180px 0px -60% 0px' },
    )
    categories.forEach((c) => {
      const el = document.getElementById(sectionId(c.slug))
      if (el) observer.observe(el)
    })
    return () => observer.disconnect()
  }, [categories])

  useEffect(() => {
    chipRefs.current[activeSlug]?.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' })
  }, [activeSlug])

  return (
    <nav aria-label="Categorías" className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
      {categories.map((c) => (
        <a
          key={c.slug}
          ref={(el) => { chipRefs.current[c.slug] = el }}
          href={`#${sectionId(c.slug)}`}
          className={`whitespace-nowrap rounded-full px-3 py-1 text-sm font-medium transition-colors ${
            c.slug === activeSlug ? 'bg-plum text-cream' : 'bg-plum/5 text-plum'
          }`}
        >
          {c.name}
        </a>
      ))}
    </nav>
  )
}
```

`menu-site/src/components/MenuItem.jsx`:

```jsx
import { formatVariant } from '../lib/format'

function Tags({ slugs, tagsBySlug }) {
  if (slugs.length === 0) return null
  return (
    <div className="mt-1 flex flex-wrap gap-1">
      {slugs.map((slug) => tagsBySlug[slug] && (
        <span key={slug} className="rounded-full px-2 py-0.5 text-xs font-medium text-white" style={{ backgroundColor: tagsBySlug[slug].color }}>
          {tagsBySlug[slug].name}
        </span>
      ))}
    </div>
  )
}

export default function MenuItem({ item, tagsBySlug, onOpenPhoto }) {
  const prices = item.variants.map(formatVariant).join(' · ')
  return (
    <li className={`flex gap-3 py-3 ${item.featured ? 'rounded-xl bg-white/70 px-3' : ''}`}>
      {item.image && (
        <button type="button" onClick={() => onOpenPhoto(item)} className="flex-shrink-0" aria-label={`Ver foto de ${item.name}`}>
          <img src={item.image} alt="" loading="lazy" className="h-20 w-20 rounded-lg object-cover" />
        </button>
      )}
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="font-bold leading-tight">
            {item.featured && <span className="mr-1 text-coral" aria-label="Destacado">★</span>}
            {item.name}
          </h3>
          {item.variants.length === 1 && <span className="whitespace-nowrap font-bold">{prices}</span>}
        </div>
        {item.description && <p className="mt-0.5 text-sm text-plum-light">{item.description}</p>}
        {item.variants.length > 1 && <p className="mt-1 text-sm font-bold">{prices}</p>}
        <Tags slugs={item.tags} tagsBySlug={tagsBySlug} />
      </div>
    </li>
  )
}
```

`menu-site/src/components/CategorySection.jsx`:

```jsx
import MenuItem from './MenuItem'
import { sectionId } from './CategoryNav'

export default function CategorySection({ category, tagsBySlug, onOpenPhoto }) {
  return (
    <section id={sectionId(category.slug)} data-slug={category.slug} className="scroll-mt-48 py-4">
      <h2 className="font-display text-3xl uppercase tracking-wide">{category.name}</h2>
      {category.description && <p className="mt-1 text-sm italic text-plum-light">{category.description}</p>}
      <ul className="mt-2 divide-y divide-plum/10">
        {category.items.map((item) => (
          <MenuItem key={item.id} item={item} tagsBySlug={tagsBySlug} onOpenPhoto={onOpenPhoto} />
        ))}
      </ul>
    </section>
  )
}
```

`menu-site/src/components/Lightbox.jsx`:

```jsx
import { useEffect } from 'react'

export default function Lightbox({ item, onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div role="dialog" aria-modal="true" aria-label={item.name} onClick={onClose} className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-plum-dark/90 p-4">
      <img src={item.image} alt={item.name} className="max-h-[80vh] max-w-full rounded-xl object-contain" />
      <p className="mt-3 font-display text-2xl uppercase text-cream">{item.name}</p>
      <button type="button" onClick={onClose} className="mt-2 text-sm text-cream underline">Cerrar</button>
    </div>
  )
}
```

`menu-site/src/components/Footer.jsx`:

```jsx
export default function Footer({ settings }) {
  const handle = (settings.instagram || '').replace(/^@/, '')
  return (
    <footer className="mt-6 rounded-t-3xl bg-plum px-6 py-8 text-center text-cream">
      {settings.footer_text && <p className="whitespace-pre-line text-sm leading-relaxed">{settings.footer_text}</p>}
      {handle && (
        <a href={`https://instagram.com/${handle}`} target="_blank" rel="noreferrer" className="mt-4 inline-block font-bold underline">
          @{handle}
        </a>
      )}
    </footer>
  )
}
```

`menu-site/src/components/MenuMessage.jsx`:

```jsx
export default function MenuMessage({ title, children }) {
  return (
    <div className="px-6 py-16 text-center">
      <p className="font-display text-3xl uppercase">{title}</p>
      {children && <p className="mt-2 text-plum-light">{children}</p>}
    </div>
  )
}
```

- [ ] **Step 2: App**

Reemplazar `menu-site/src/App.jsx`:

```jsx
import { useEffect, useMemo, useState } from 'react'
import { loadMenu } from './lib/loadMenu'
import { filterMenu } from './lib/filterMenu'
import Header from './components/Header'
import SearchBar from './components/SearchBar'
import TagFilters from './components/TagFilters'
import CategoryNav from './components/CategoryNav'
import CategorySection from './components/CategorySection'
import Lightbox from './components/Lightbox'
import Footer from './components/Footer'
import MenuMessage from './components/MenuMessage'

const MENU_URL = import.meta.env.VITE_MENU_URL || '/menu.sample.json'

export default function App() {
  const [state, setState] = useState({ status: 'loading', menu: null })
  const [query, setQuery] = useState('')
  const [activeTags, setActiveTags] = useState([])
  const [photoItem, setPhotoItem] = useState(null)

  useEffect(() => {
    loadMenu({ url: MENU_URL })
      .then(({ menu }) => setState({ status: 'ready', menu }))
      .catch(() => setState({ status: 'error', menu: null }))
  }, [])

  const menu = state.menu
  const categories = useMemo(
    () => (menu ? filterMenu(menu.categories, { query, tagSlugs: activeTags }) : []),
    [menu, query, activeTags],
  )
  const tagsBySlug = useMemo(() => Object.fromEntries((menu?.tags || []).map((t) => [t.slug, t])), [menu])

  const toggleTag = (slug) =>
    setActiveTags((tags) => (tags.includes(slug) ? tags.filter((t) => t !== slug) : [...tags, slug]))

  return (
    <div className="mx-auto min-h-screen max-w-xl">
      <Header />
      {state.status === 'loading' && <MenuMessage title="Cargando la carta…" />}
      {state.status === 'error' && (
        <MenuMessage title="No pudimos cargar la carta">Pedile la carta a nuestro equipo 💛</MenuMessage>
      )}
      {state.status === 'ready' && (
        <>
          <div className="sticky top-0 z-10 space-y-2 bg-cream/95 px-4 pb-3 pt-2 backdrop-blur">
            <SearchBar value={query} onChange={setQuery} />
            <TagFilters tags={menu.tags} active={activeTags} onToggle={toggleTag} />
            <CategoryNav categories={categories} />
          </div>
          <main className="px-4">
            {categories.length === 0 ? (
              <MenuMessage title="Sin resultados">Probá con otra palabra o sacá algún filtro.</MenuMessage>
            ) : (
              categories.map((category) => (
                <CategorySection key={category.slug} category={category} tagsBySlug={tagsBySlug} onOpenPhoto={setPhotoItem} />
              ))
            )}
          </main>
          <Footer settings={menu.settings} />
        </>
      )}
      {photoItem && <Lightbox item={photoItem} onClose={() => setPhotoItem(null)} />}
    </div>
  )
}
```

- [ ] **Step 3: Datos de ejemplo para desarrollo**

Generar `menu-site/public/menu.sample.json` desde la base local (con la carta del seed y al menos una foto y un tag cargados):

```bash
cd backend && python -c "
import json
from dotenv import load_dotenv; load_dotenv()
from app import create_app
from app.services.menu_publish_service import build_snapshot
app = create_app('development')
with app.app_context():
    json.dump({**build_snapshot(), 'published_at': '2026-10-07T00:00:00Z'}, open('../menu-site/public/menu.sample.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
"
```

Expected: el archivo existe y tiene `"version": 1`.

- [ ] **Step 4: Verificar**

Run: `cd menu-site && npm test && npm run build`
Expected: tests pasan, build OK.

Manual con `npm run dev` en `http://localhost:5174`, en vista mobile (375px) del navegador:
1. Se ven todas las categorías; la barra de chips queda fija al scrollear y resalta la sección actual.
2. Tocar un chip lleva a la sección sin que el título quede tapado.
3. Buscar "cafe" encuentra "Café…"; buscar algo inexistente muestra "Sin resultados".
4. Filtros de tags se combinan.
5. Ítems con dos precios muestran `Porción $11.200 · Entera $12.600`.
6. Tocar una foto abre el lightbox; Escape o tocar cierra.
7. Con devtools → Network "Offline" y recargar: la carta sigue apareciendo (caché). Borrar localStorage + offline → mensaje "Pedile la carta a nuestro equipo".
8. Sin scroll horizontal en 320px.

(Las imágenes de marca dan 404 hasta Task 20; está bien en este paso.)

- [ ] **Step 5: Commit**

```bash
git add menu-site/src menu-site/public/menu.sample.json
git commit -m "feat(menu-site): menu UI with sticky categories, search, tags and photos"
```

---

### Task 20: Assets de marca

**Files:**
- Create: `menu-site/public/brand/logo.png`, `flower-lime.png`, `flower-coral.png`, `favicon.png`

Fuentes (carpetas de Drive compartidas por link):
- Logos transparentes: `https://drive.google.com/drive/folders/1lr_XXH-jmiKS3EEqYWCfU0PDIvB2ywzs` ("Logos fondo Transp", `Galia_Logos_Transp (1..12).png`)
- Ilustraciones: `https://drive.google.com/drive/folders/1cSEcMuVWjwoTIR4neUK8j1X9C4ncLgXC` ("ILUSTRACIONES", PNGs + `Ilustraciones Galia 2.pdf`)

- [ ] **Step 1: Elegir y descargar** (pedir confirmación al usuario antes de descargar)

- Logo: la variante transparente en **bordó** que incluye "GALIA" + taza con flor (la de la portada del PDF). Guardar como `menu-site/public/brand/logo-original.png`.
- Flores: de "ILUSTRACIONES", la(s) imagen(es) con la flor lima y la flor coral. Guardar como `menu-site/public/brand/flowers-original.png` (o dos archivos si vienen separadas).
- Favicon: variante transparente solo con la taza/flor (o el logo completo si no hay).

- [ ] **Step 2: Optimizar**

```bash
cd menu-site/public/brand && python -c "
from PIL import Image
def save(src, dst, max_side):
    im = Image.open(src).convert('RGBA')
    im = im.crop(im.getbbox())
    im.thumbnail((max_side, max_side))
    im.save(dst, optimize=True)
    print(dst, im.size)
save('logo-original.png', 'logo.png', 480)
save('logo-original.png', 'favicon.png', 64)
"
```

Para las flores: si vienen en una sola lámina, recortar cada flor con `Image.open(...).crop((x0, y0, x1, y1))` (coordenadas medidas abriendo la imagen) y aplicar `save(..., 'flower-lime.png', 200)` / `save(..., 'flower-coral.png', 200)`. Borrar los `*-original.png` después.

Expected: `logo.png` < 80 KB, cada flor < 30 KB.

- [ ] **Step 3: Verificar**

`npm run dev` → el header muestra el logo centrado con una flor lima arriba a la izquierda y una coral a la derecha, sin tapar el logo en 320px. El favicon aparece en la pestaña.

- [ ] **Step 4: Commit**

```bash
git add menu-site/public/brand
git commit -m "feat(menu-site): add Galia brand assets"
```

---

## Phase D — Infraestructura y puesta en marcha

### Task 21: AWS — prefijo público `menu/` en el bucket existente (manual, lo hace el usuario)

- [ ] **Step 1: Block Public Access**

Consola S3 → bucket (valor de `AWS_S3_BUCKET_NAME`) → Permissions → Block public access → Edit:
- ✅ Block public access to buckets and objects granted through *new* ACLs
- ✅ Block public access to buckets and objects granted through *any* ACLs
- ⬜ Block public access … through *new* public bucket or access point policies
- ⬜ Block public and cross-account access … through *any* public bucket or access point policies

- [ ] **Step 2: Bucket policy** (Permissions → Bucket policy; reemplazar `<bucket>`; si ya hay una policy, agregar solo el statement)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadMenuPrefixOnly",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::<bucket>/menu/*"
    }
  ]
}
```

- [ ] **Step 3: CORS** (Permissions → Cross-origin resource sharing)

```json
[
  {
    "AllowedOrigins": ["https://galia-carta.onrender.com", "http://localhost:5174"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3600
  }
]
```

- [ ] **Step 4: Verificar privacidad**

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://<bucket>.s3.<region>.amazonaws.com/menu/menu.json
curl -s -o /dev/null -w "%{http_code}\n" https://<bucket>.s3.<region>.amazonaws.com/absence-attachments/
```

Expected: el primero `200` (después de publicar al menos una vez) o `403`/`404` antes; el segundo **siempre `403`**. Si el segundo da `200`, revertir la policy y revisar el `Resource`.

---

### Task 22: Render — sitio de la carta, cron y variables

**Files:**
- Modify: `render.yaml`

- [ ] **Step 1: Agregar servicios**

En `render.yaml`, dentro de `services:` después del servicio `galia-frontend` (antes de `databases:`):

```yaml
  # Carta pública (sitio estático)
  - type: web
    name: galia-carta
    env: static
    buildCommand: "cd menu-site && npm install && npm run build"
    staticPublishPath: menu-site/dist
    envVars:
      - key: VITE_MENU_URL
        sync: false

  # Sync nocturno de la carta con Fudo (04:00 hora Argentina = 07:00 UTC)
  - type: cron
    name: galia-menu-sync
    env: python
    region: oregon
    plan: starter
    schedule: "0 7 * * *"
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "cd backend && python -m app.tasks.menu_tasks"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: FLASK_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: galia-db
          property: connectionString
      - key: FUDO_API_KEY
        sync: false
      - key: FUDO_API_SECRET
        sync: false
      - key: AWS_ACCESS_KEY_ID
        sync: false
      - key: AWS_SECRET_ACCESS_KEY
        sync: false
      - key: AWS_REGION
        sync: false
      - key: AWS_S3_BUCKET_NAME
        sync: false
      - key: MENU_PUBLIC_BASE_URL
        sync: false
```

y en `envVars` del servicio `galia-backend` agregar:

```yaml
      - key: MENU_PUBLIC_BASE_URL
        sync: false
```

y en `envVars` de `galia-frontend` agregar:

```yaml
      - key: VITE_PUBLIC_MENU_URL
        value: https://galia-carta.onrender.com
```

- [ ] **Step 2: Validar YAML**

Run: `python -c "import yaml,sys; yaml.safe_load(open('render.yaml')); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add render.yaml
git commit -m "chore(render): add public menu site and nightly menu sync cron"
```

- [ ] **Step 4: Cargar variables en Render (manual, lo hace el usuario)**

- `galia-backend` y `galia-menu-sync`: `MENU_PUBLIC_BASE_URL=https://<bucket>.s3.<region>.amazonaws.com/menu`
- `galia-menu-sync`: mismas `FUDO_*` y `AWS_*` que `galia-backend`
- `galia-carta`: `VITE_MENU_URL=https://<bucket>.s3.<region>.amazonaws.com/menu/menu.json`

> El cron job de Render es de pago (plan starter). Si no se quiere pagar, quitar el servicio `galia-menu-sync`: la carta funciona igual con el botón "Sincronizar Fudo" + "Publicar".

---

### Task 23: Verificación end-to-end y salida a producción

- [ ] **Step 1: Suite completa**

Run: `cd backend && pytest tests/ -q`
Expected: los tests de la carta pasan y los preexistentes mantienen el mismo resultado que en `main`.

Run: `cd frontend && npm run build` y `cd menu-site && npm test && npm run build`
Expected: sin errores.

- [ ] **Step 2: Flujo completo en local** (con AWS configurado y `MENU_PUBLIC_BASE_URL` / `VITE_MENU_URL` apuntando al bucket real)

1. `python seed_menu.py` (si la base está vacía).
2. En `/menu`: "Sincronizar Fudo" → mensaje con cantidad de productos.
3. `/menu/inbox`: vincular al menos 5 productos (crear ítem / agregar a ítem existente).
4. Subir una foto a un ítem; crear tag "Sin TACC" y asignarlo.
5. "Publicar" → `curl https://<bucket>.s3.<region>.amazonaws.com/menu/menu.json` devuelve el JSON con los cambios.
6. `menu-site` con `VITE_MENU_URL` real: la carta muestra los datos publicados, foto incluida.
7. Cambiar un precio en Fudo → `cd backend && python -m app.tasks.menu_tasks` → log con `price_changes: 1, published: True` → la carta muestra el precio nuevo (≤ 60 s).

- [ ] **Step 3: Deploy**

Mergear `feature/carta-digital` (PR) → Render despliega backend (`flask db upgrade` corre en `build.sh`), frontend, `galia-carta` y el cron. En producción: `python seed_menu.py` una vez desde la shell de Render del backend, vincular con Fudo y publicar.

- [ ] **Step 4: QR**

Generar el QR apuntando a `https://galia-carta.onrender.com` y probarlo con 2 celulares (iOS y Android) en el local antes de reemplazar los QR de las mesas.
