"""Vouchers de descuento: tandas, vouchers con código único e historial de cambios de la tanda.

El estado de un voucher (en uso, canjeado) no se guarda: se deriva del descuento activo del POS
que lo referencia (`pos_discounts.voucher_id`)."""
from datetime import datetime

from app.extensions import db


class VoucherBatch(db.Model):
    __tablename__ = 'voucher_batches'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    min_sale_amount = db.Column(db.Numeric(12, 2), nullable=True)
    expires_at = db.Column(db.Date, nullable=False)
    terms = db.Column(db.Text, nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vouchers = db.relationship('Voucher', back_populates='batch', order_by='Voucher.id')


class Voucher(db.Model):
    __tablename__ = 'vouchers'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('voucher_batches.id'), nullable=False, index=True)
    code = db.Column(db.String(20), nullable=False, unique=True, index=True)
    voided_at = db.Column(db.DateTime, nullable=True)
    voided_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    void_reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    batch = db.relationship('VoucherBatch', back_populates='vouchers')


class VoucherChangeLog(db.Model):
    __tablename__ = 'voucher_change_log'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('voucher_batches.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    field = db.Column(db.String(50), nullable=False)
    old_value = db.Column(db.String(100), nullable=True)
    new_value = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
