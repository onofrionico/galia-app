from datetime import datetime

from app.extensions import db
from app.utils.menu_storage import public_url

menu_item_tags = db.Table(
    'menu_item_tags',
    db.Column('item_id', db.Integer, db.ForeignKey('menu_items.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('menu_tags.id', ondelete='CASCADE'), primary_key=True),
)


class MenuGroup(db.Model):
    """Sección de presentación de la carta pública (agrupa categorías). No afecta productos."""
    __tablename__ = 'menu_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), nullable=False, unique=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Sin passive_deletes: al borrar el grupo SQLAlchemy pone group_id = NULL (también en SQLite).
    categories = db.relationship('MenuCategory', backref='group')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'slug': self.slug, 'sort_order': self.sort_order}


class MenuCategory(db.Model):
    __tablename__ = 'menu_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)
    fudo_category_id = db.Column(db.String(20), unique=True)
    group_id = db.Column(db.Integer, db.ForeignKey('menu_groups.id', ondelete='SET NULL'), index=True)
    show_title = db.Column(db.Boolean, nullable=False, default=True)
    fudo_status = db.Column(db.String(20))  # None | 'missing'
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
            'fudo_category_id': self.fudo_category_id,
            'group_id': self.group_id,
            'show_title': self.show_title,
            'fudo_status': self.fudo_status,
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
    reviewed_at = db.Column(db.DateTime)
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
            'reviewed': self.reviewed_at is not None,
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
    fudo_category_id = db.Column(db.String(20))
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
            'fudo_category_id': self.fudo_category_id,
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
