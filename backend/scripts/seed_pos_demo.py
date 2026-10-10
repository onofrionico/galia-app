"""Carga datos de prueba para el POS: usuarios, catálogo con modificadores, salones, mesas y plantillas.

Uso (desde backend/, con DATABASE_URL apuntando a una base DESCARTABLE ya migrada):
    python scripts/seed_pos_demo.py

Es idempotente: si ya existe el salón "Salón principal" no hace nada.
Usuarios de prueba (contraseña DEMO_PASSWORD):
    admin@galia.test  admin
    caja@galia.test   POS, Cobrar, Anular, Descuentos
    mozo@galia.test   Camarero
"""
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Module, Product, ProductCategory, ProductVariant, User, UserPermission  # noqa: E402
from app.models.pos import (DiscountTemplate, ModifierGroup, ModifierOption, PosTable,  # noqa: E402
                            ProductModifierGroup, Salon)

DEMO_PASSWORD = 'galia-demo-2026'


def _user(email, role, modules=()):
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(email=email, role=role, is_active=True)
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        db.session.flush()
    for name in modules:
        module = Module.query.filter_by(name=name).one()
        if UserPermission.query.filter_by(user_id=user.id, module_id=module.id).first() is None:
            db.session.add(UserPermission(user_id=user.id, module_id=module.id, is_granted=True))
    return user


def _group(name, min_select, max_select, options):
    group = ModifierGroup(name=name, min_select=min_select, max_select=max_select)
    db.session.add(group)
    db.session.flush()
    for position, (option_name, delta) in enumerate(options):
        db.session.add(ModifierOption(group_id=group.id, name=option_name, price_delta=Decimal(delta),
                                      position=position))
    return group


def _product(category, name, variants, groups=()):
    product = Product(name=name, category_id=category.id, has_recipe=False, track_stock=False)
    db.session.add(product)
    db.session.flush()
    for variant_name, price in variants:
        db.session.add(ProductVariant(product_id=product.id, name=variant_name, price=Decimal(price),
                                      stock_quantity=0, min_stock=0))
    for position, group in enumerate(groups):
        db.session.add(ProductModifierGroup(product_id=product.id, group_id=group.id, position=position))
    return product


def seed():
    if Salon.query.filter_by(name='Salón principal').first():
        print('Ya hay datos de prueba.')
        return
    _user('admin@galia.test', 'admin')
    _user('caja@galia.test', 'employee', ('POS', 'Cobrar', 'Anular', 'Descuentos'))
    _user('mozo@galia.test', 'employee', ('Camarero',))

    cafeteria = ProductCategory(name='Cafetería')
    panaderia = ProductCategory(name='Panadería')
    sandwiches = ProductCategory(name='Sandwiches')
    db.session.add_all([cafeteria, panaderia, sandwiches])
    db.session.flush()
    leche = _group('Leche', 1, 1, [('Entera', '0'), ('Descremada', '0'), ('Almendras', '500')])
    pan = _group('Pan', 1, 1, [('Blanco', '0'), ('Integral', '300'), ('Sin TACC', '800')])
    extras = _group('Extras', 0, 3, [('Huevo', '600'), ('Palta', '900'), ('Sin tomate', '0')])
    _product(cafeteria, 'Latte', [('Chico', '3500'), ('Grande', '4200')], [leche])
    _product(cafeteria, 'Cortado', [('Taza', '2800')], [leche])
    _product(cafeteria, 'Espresso', [('Taza', '2500')])
    _product(panaderia, 'Medialuna', [('Unidad', '900')])
    _product(panaderia, 'Budín de limón', [('Porción', '2600')])
    _product(sandwiches, 'Tostado jamón y queso', [('Unidad', '6500')], [pan, extras])

    principal = Salon(name='Salón principal', position=0)
    terraza = Salon(name='Terraza', position=1)
    db.session.add_all([principal, terraza])
    db.session.flush()
    for number, x, y, width, height in [(1, 4, 4, 12, 10), (2, 20, 4, 12, 10), (3, 36, 4, 12, 10),
                                        (4, 4, 20, 20, 12), (5, 30, 22, 10, 10), (6, 60, 4, 8, 30)]:
        db.session.add(PosTable(salon_id=principal.id, number=number, pos_x=x, pos_y=y, width=width, height=height))
    for number in (1, 2):
        db.session.add(PosTable(salon_id=terraza.id, number=number, pos_x=4 + 16 * (number - 1), pos_y=4,
                                width=12, height=10))

    db.session.add_all([
        DiscountTemplate(name='Empleado', kind='percent', value=Decimal('20'), scope='sale', restricted=True),
        DiscountTemplate(name='Happy hour', kind='percent', value=Decimal('15'), scope='sale', restricted=False),
        DiscountTemplate(name='Cortesía', kind='percent', value=Decimal('100'), scope='item', restricted=False),
    ])
    db.session.commit()
    print('Datos de prueba cargados.')


if __name__ == '__main__':
    app = create_app(os.environ.get('FLASK_ENV', 'production'))
    with app.app_context():
        seed()
