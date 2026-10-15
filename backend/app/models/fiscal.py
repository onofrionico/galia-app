"""Facturación electrónica ARCA: configuración, token WSAA, clientes y comprobantes."""
from app.extensions import db

SETTINGS_ID = 1
VOUCHER_TYPES = {1: ('invoice', 'A'), 3: ('credit_note', 'A'), 6: ('invoice', 'B'), 8: ('credit_note', 'B'),
                 11: ('invoice', 'C'), 13: ('credit_note', 'C')}
INVOICE_STATUSES = ('pending', 'authorized', 'rejected')
ENVIRONMENTS = ('homologacion', 'produccion')
EMITTER_CONDITIONS = ('monotributo', 'responsable_inscripto')
RECEIVER_CONDITIONS = ('consumidor_final', 'monotributo', 'responsable_inscripto', 'exento')


class FiscalSettings(db.Model):
    """Configuración fiscal. Una sola fila (id = SETTINGS_ID). Las claves privadas van cifradas."""
    __tablename__ = 'fiscal_settings'

    id = db.Column(db.Integer, primary_key=True)
    cuit = db.Column(db.String(11), nullable=True)
    business_name = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    gross_income = db.Column(db.String(40), nullable=True)
    activity_start = db.Column(db.Date, nullable=True)
    iva_condition = db.Column(db.String(30), nullable=False, default='monotributo')
    point_of_sale = db.Column(db.Integer, nullable=True)
    environment = db.Column(db.String(15), nullable=False, default='homologacion')
    cf_id_threshold = db.Column(db.Numeric(14, 2), nullable=True)
    default_iva_rate = db.Column(db.Numeric(5, 2), nullable=False, default=21)
    homo_private_key = db.Column(db.Text, nullable=True)
    homo_csr = db.Column(db.Text, nullable=True)
    homo_certificate = db.Column(db.Text, nullable=True)
    homo_cert_expires_at = db.Column(db.DateTime, nullable=True)
    prod_private_key = db.Column(db.Text, nullable=True)
    prod_csr = db.Column(db.Text, nullable=True)
    prod_certificate = db.Column(db.Text, nullable=True)
    prod_cert_expires_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)

    @staticmethod
    def prefix(environment):
        return 'homo' if environment == 'homologacion' else 'prod'

    def credential(self, environment, name):
        return getattr(self, f'{self.prefix(environment)}_{name}')

    def set_credential(self, environment, name, value):
        setattr(self, f'{self.prefix(environment)}_{name}', value)


class ArcaToken(db.Model):
    __tablename__ = 'arca_tokens'
    __table_args__ = (db.UniqueConstraint('service', 'environment', name='uq_arca_tokens_service_env'),)

    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(20), nullable=False)
    environment = db.Column(db.String(15), nullable=False)
    token = db.Column(db.Text, nullable=False)
    sign = db.Column(db.Text, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)


class FiscalCustomer(db.Model):
    __tablename__ = 'fiscal_customers'
    __table_args__ = (db.UniqueConstraint('doc_type', 'doc_number', name='uq_fiscal_customers_doc'),)

    id = db.Column(db.Integer, primary_key=True)
    doc_type = db.Column(db.String(5), nullable=False)
    doc_number = db.Column(db.String(11), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    iva_condition = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {'id': self.id, 'doc_type': self.doc_type, 'doc_number': self.doc_number, 'name': self.name,
                'iva_condition': self.iva_condition, 'address': self.address}


class Invoice(db.Model):
    __tablename__ = 'invoices'
    __table_args__ = (
        db.Index('ix_invoices_sale_id', 'sale_id'),
        db.Index('ix_invoices_related_invoice_id', 'related_invoice_id'),
        # Nunca dos comprobantes autorizados con el mismo número.
        db.Index('uq_invoices_authorized_number', 'environment', 'point_of_sale', 'voucher_type', 'number',
                 unique=True, postgresql_where=db.text("status = 'authorized'"),
                 sqlite_where=db.text("status = 'authorized'")),
    )

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(15), nullable=False)
    voucher_type = db.Column(db.Integer, nullable=False)
    environment = db.Column(db.String(15), nullable=False)
    point_of_sale = db.Column(db.Integer, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=True)
    related_invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('fiscal_customers.id'), nullable=True)
    receiver_doc_type = db.Column(db.Integer, nullable=False)
    receiver_doc_number = db.Column(db.String(11), nullable=False)
    receiver_name = db.Column(db.String(120), nullable=False)
    receiver_iva_condition = db.Column(db.String(30), nullable=False)
    receiver_address = db.Column(db.String(200), nullable=True)
    detail_mode = db.Column(db.String(10), nullable=False)
    lines = db.Column(db.JSON, nullable=False)
    total = db.Column(db.Numeric(14, 2), nullable=False)
    net = db.Column(db.Numeric(14, 2), nullable=False)
    iva = db.Column(db.Numeric(14, 2), nullable=False)
    iva_rate = db.Column(db.Numeric(5, 2), nullable=False)
    voucher_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    cae = db.Column(db.String(20), nullable=True)
    cae_due = db.Column(db.Date, nullable=True)
    arca_result = db.Column(db.JSON, nullable=True)
    request = db.Column(db.JSON, nullable=False)
    error = db.Column(db.String(500), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    authorized_at = db.Column(db.DateTime, nullable=True)

    sale = db.relationship('PosSale')
    related = db.relationship('Invoice', remote_side=[id])
    payments = db.relationship('InvoicePayment', backref='invoice', cascade='all, delete-orphan')

    @property
    def letter(self):
        return VOUCHER_TYPES[self.voucher_type][1]

    @property
    def is_credit_note(self):
        return VOUCHER_TYPES[self.voucher_type][0] == 'credit_note'

    @property
    def label(self):
        name = 'Nota de crédito' if self.is_credit_note else 'Factura'
        return f'{name} {self.letter} {self.point_of_sale:05d}-{self.number:08d}'


class InvoicePayment(db.Model):
    __tablename__ = 'invoice_payments'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('pos_payments.id'), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
