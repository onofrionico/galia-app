"""Fábricas compartidas por los tests de caja."""
from types import SimpleNamespace

from app.extensions import db
from app.models.pos import CashRegister, PaymentMethod


def make_register(name='Caja principal'):
    register = CashRegister(name=name)
    db.session.add(register)
    db.session.commit()
    return register


def make_methods():
    efectivo = PaymentMethod(name='Efectivo', kind='cash', position=0)
    debito = PaymentMethod(name='Débito', kind='card', position=1)
    db.session.add_all([efectivo, debito])
    db.session.commit()
    return SimpleNamespace(efectivo=efectivo, debito=debito)
