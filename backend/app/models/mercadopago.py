"""MercadoPago: configuración, cobros con Point, movimientos de la cuenta y resoluciones de conciliación."""
from app.extensions import db

SETTINGS_ID = 1
ENVIRONMENTS = ('test', 'production')
ACTIVE_STATUSES = ('creating', 'created', 'processing', 'canceling')
FINAL_STATUSES = ('approved', 'failed', 'canceled', 'expired')
RESOLUTION_KINDS = ('matched_manual', 'payment_created', 'not_a_sale', 'reviewed')
_ACTIVE_WHERE = "status IN ('creating', 'created', 'processing', 'canceling')"


class MpSettings(db.Model):
    """Una sola fila. Los tokens y el secreto del webhook van cifrados."""
    __tablename__ = 'mp_settings'

    id = db.Column(db.Integer, primary_key=True)
    environment = db.Column(db.String(12), nullable=False, default='test')
    test_access_token = db.Column(db.Text, nullable=True)
    prod_access_token = db.Column(db.Text, nullable=True)
    terminal_id = db.Column(db.String(80), nullable=True)
    webhook_secret = db.Column(db.Text, nullable=True)
    point_payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'), nullable=True)
    user_id = db.Column(db.String(30), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)

    def token(self, environment):
        return self.prod_access_token if environment == 'production' else self.test_access_token

    def set_token(self, environment, value):
        if environment == 'production':
            self.prod_access_token = value
        else:
            self.test_access_token = value


class MpPointOrder(db.Model):
    __tablename__ = 'mp_point_orders'
    __table_args__ = (
        db.Index('ix_mp_point_orders_sale_id', 'sale_id'),
        # Un cobro activo por terminal.
        db.Index('uq_mp_point_orders_active_terminal', 'terminal_id', unique=True,
                 postgresql_where=db.text(_ACTIVE_WHERE), sqlite_where=db.text(_ACTIVE_WHERE)),
    )

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    terminal_id = db.Column(db.String(80), nullable=False)
    mp_order_id = db.Column(db.String(80), nullable=True, unique=True)
    external_reference = db.Column(db.String(64), nullable=False, unique=True)
    idempotency_key = db.Column(db.String(64), nullable=False, unique=True)
    status = db.Column(db.String(12), nullable=False)
    status_detail = db.Column(db.String(80), nullable=True)
    error = db.Column(db.String(255), nullable=True)
    mp_payment_id = db.Column(db.String(80), nullable=True)
    approved_amount = db.Column(db.Numeric(12, 2), nullable=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('pos_payments.id'), nullable=True)
    refunded_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    last_checked_at = db.Column(db.DateTime, nullable=True)

    sale = db.relationship('PosSale')
    payment = db.relationship('PosPayment')


class MpMovement(db.Model):
    __tablename__ = 'mp_movements'

    id = db.Column(db.Integer, primary_key=True)
    mp_payment_id = db.Column(db.String(80), nullable=False, unique=True)
    date_created = db.Column(db.DateTime, nullable=False)
    business_date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    refunded_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    net_amount = db.Column(db.Numeric(14, 2), nullable=True)
    currency = db.Column(db.String(5), nullable=True)
    status = db.Column(db.String(30), nullable=False)
    status_detail = db.Column(db.String(80), nullable=True)
    channel = db.Column(db.String(12), nullable=False)
    payment_type = db.Column(db.String(30), nullable=True)
    payment_method = db.Column(db.String(30), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    external_reference = db.Column(db.String(64), nullable=True, index=True)
    payer_label = db.Column(db.String(120), nullable=True)
    raw = db.Column(db.JSON, nullable=True)
    fetched_at = db.Column(db.DateTime, nullable=False)


class MpReconciliation(db.Model):
    __tablename__ = 'mp_reconciliations'
    __table_args__ = (
        db.Index('uq_mp_reconciliations_movement', 'mp_movement_id', unique=True,
                 postgresql_where=db.text('mp_movement_id IS NOT NULL'),
                 sqlite_where=db.text('mp_movement_id IS NOT NULL')),
        db.Index('uq_mp_reconciliations_payment', 'payment_id', unique=True,
                 postgresql_where=db.text('payment_id IS NOT NULL'), sqlite_where=db.text('payment_id IS NOT NULL')),
    )

    id = db.Column(db.Integer, primary_key=True)
    mp_movement_id = db.Column(db.Integer, db.ForeignKey('mp_movements.id'), nullable=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('pos_payments.id'), nullable=True)
    kind = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
