"""Fábricas compartidas por los tests de impresión."""
from decimal import Decimal
from types import SimpleNamespace

from app.extensions import db
from app.models import Product, ProductCategory, ProductVariant
from app.models.pos import PrintPoint, PrintStation, Printer


def make_station(name='Cocina'):
    station = PrintStation(name=name)
    db.session.add(station)
    db.session.commit()
    return station


def make_printer(name, station=None, cashier=False, point='Caja', connection='network', width=80, active=True):
    printer = Printer(name=name, connection=connection, host='192.168.0.50' if connection == 'network' else None,
                      port=9100, os_name='EPSON TM-T20' if connection == 'usb' else None, paper_width=width,
                      print_point=point, station_id=station.id if station else None, is_cashier=cashier,
                      is_active=active)
    db.session.add(printer)
    if db.session.get(PrintPoint, point) is None:
        db.session.add(PrintPoint(name=point))
    db.session.commit()
    return printer


def make_kitchen_product():
    category = ProductCategory(name='Platos')
    db.session.add(category)
    db.session.flush()
    product = Product(name='Tostado', category_id=category.id, has_recipe=False)
    db.session.add(product)
    db.session.flush()
    variant = ProductVariant(product_id=product.id, name='Unidad', price=Decimal('3000'), stock_quantity=0,
                             min_stock=0)
    db.session.add(variant)
    db.session.commit()
    return SimpleNamespace(category=category, product=product, variant=variant)
