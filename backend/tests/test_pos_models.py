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


def test_deleting_item_does_not_null_discount_item_id(app):
    from datetime import date, datetime
    from app.models import ProductVariant, User
    from app.models.pos import PosDiscount, PosSale, PosSaleItem

    user = User(email='u2@test.com', role='admin', is_active=True)
    user.set_password('secret123')
    cat = ProductCategory(name='Cafés')
    db.session.add_all([user, cat])
    db.session.flush()
    product = Product(name='Cortado', category_id=cat.id)
    db.session.add(product)
    db.session.flush()
    variant = ProductVariant(product_id=product.id, name='Taza', price=2000, stock_quantity=0, min_stock=0)
    db.session.add(variant)
    db.session.flush()
    sale = PosSale(business_date=date.today(), number=1, sale_type='counter', status='open',
                   opened_at=datetime.utcnow(), opened_by=user.id)
    item = PosSaleItem(product_variant_id=variant.id, product_name='Cortado', variant_name='Taza',
                       unit_price=2000, quantity=1, modifiers_total=0, line_total=2000,
                       created_by=user.id, created_at=datetime.utcnow())
    sale.items.append(item)
    db.session.add(sale)
    db.session.flush()
    discount = PosDiscount(sale=sale, item=item, kind='amount', value=100, amount=100, created_by=user.id,
                           created_at=datetime.utcnow())
    db.session.add(discount)
    db.session.flush()
    discount_id, item_id = discount.id, item.id

    sale.items.remove(item)
    db.session.flush()
    db.session.expire_all()

    assert db.session.get(PosDiscount, discount_id).item_id == item_id
