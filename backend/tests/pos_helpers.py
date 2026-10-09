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
