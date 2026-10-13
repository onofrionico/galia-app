from app.extensions import db

CASH_SESSION_STATUSES = ('open', 'closed')
CASH_MOVEMENT_KINDS = ('opening_float', 'expense', 'withdrawal', 'deposit')


class CashRegister(db.Model):
    __tablename__ = 'cash_registers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False, unique=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class CashSession(db.Model):
    __tablename__ = 'cash_sessions'
    # Una sola sesión abierta por caja; el servicio además lo valida con bloqueo de fila.
    __table_args__ = (
        db.Index('uq_cash_sessions_open_register', 'register_id', unique=True,
                 postgresql_where=db.text("status = 'open'"), sqlite_where=db.text("status = 'open'")),
    )

    id = db.Column(db.Integer, primary_key=True)
    register_id = db.Column(db.Integer, db.ForeignKey('cash_registers.id'), nullable=False, index=True)
    status = db.Column(db.String(10), nullable=False, default='open')
    opened_at = db.Column(db.DateTime, nullable=False)
    opened_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    opening_float = db.Column(db.Numeric(12, 2), nullable=False)
    closed_at = db.Column(db.DateTime, nullable=True)
    closed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    closing_note = db.Column(db.String(500), nullable=True)

    register = db.relationship('CashRegister')
    opener = db.relationship('User', foreign_keys=[opened_by])
    closer = db.relationship('User', foreign_keys=[closed_by])
    movements = db.relationship('CashMovement', back_populates='session', order_by='CashMovement.id')
    counts = db.relationship('CashSessionCount', back_populates='session', order_by='CashSessionCount.id',
                             cascade='all, delete-orphan')


class CashMovement(db.Model):
    __tablename__ = 'cash_movements'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_sessions.id'), nullable=False, index=True)
    kind = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancel_reason = db.Column(db.String(255), nullable=True)

    session = db.relationship('CashSession', back_populates='movements')
    creator = db.relationship('User', foreign_keys=[created_by])

    @property
    def is_active(self):
        return self.cancelled_at is None


class CashSessionCount(db.Model):
    __tablename__ = 'cash_session_counts'
    __table_args__ = (db.UniqueConstraint('session_id', 'payment_method_id', name='uq_cash_session_counts_method'),)

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_sessions.id'), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'), nullable=False)
    method_name = db.Column(db.String(50), nullable=False)
    expected = db.Column(db.Numeric(12, 2), nullable=False)
    counted = db.Column(db.Numeric(12, 2), nullable=False)
    difference = db.Column(db.Numeric(12, 2), nullable=False)

    session = db.relationship('CashSession', back_populates='counts')


class CashEvent(db.Model):
    __tablename__ = 'cash_events'

    id = db.Column(db.Integer, primary_key=True)
    register_id = db.Column(db.Integer, db.ForeignKey('cash_registers.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_sessions.id'), nullable=True, index=True)
    kind = db.Column(db.String(30), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    payload = db.Column(db.JSON, nullable=False, default=dict)

    user = db.relationship('User')
