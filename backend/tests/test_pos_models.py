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
