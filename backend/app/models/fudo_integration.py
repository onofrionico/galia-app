from datetime import datetime
from app.extensions import db

class FudoSyncLog(db.Model):
    __tablename__ = 'fudo_sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    sync_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    records_processed = db.Column(db.Integer, default=0)
    records_created = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)
    records_failed = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    sync_metadata = db.Column(db.JSON)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sync_type': self.sync_type,
            'status': self.status,
            'records_processed': self.records_processed,
            'records_created': self.records_created,
            'records_updated': self.records_updated,
            'records_failed': self.records_failed,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'sync_metadata': self.sync_metadata
        }

class FudoOrder(db.Model):
    __tablename__ = 'fudo_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    fudo_order_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=True)
    order_data = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    event_type = db.Column(db.String(50))
    synced_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sale = db.relationship('Sale', backref='fudo_order', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'fudo_order_id': self.fudo_order_id,
            'sale_id': self.sale_id,
            'order_data': self.order_data,
            'status': self.status,
            'event_type': self.event_type,
            'synced_at': self.synced_at.isoformat() if self.synced_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class FudoExpense(db.Model):
    __tablename__ = 'fudo_expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    fudo_expense_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)
    expense_data = db.Column(db.JSON, nullable=False)
    synced_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    expense = db.relationship('Expense', backref='fudo_expense', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'fudo_expense_id': self.fudo_expense_id,
            'expense_id': self.expense_id,
            'expense_data': self.expense_data,
            'synced_at': self.synced_at.isoformat() if self.synced_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class FudoCashMovement(db.Model):
    __tablename__ = 'fudo_cash_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    fudo_movement_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    movement_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    cash_register = db.Column(db.String(100))
    payment_method = db.Column(db.String(100))
    description = db.Column(db.Text)
    movement_date = db.Column(db.DateTime, nullable=False)
    movement_data = db.Column(db.JSON, nullable=False)
    synced_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_fudo_cash_movements_date', 'movement_date'),
        db.Index('idx_fudo_cash_movements_type', 'movement_type'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'fudo_movement_id': self.fudo_movement_id,
            'movement_type': self.movement_type,
            'amount': float(self.amount) if self.amount else 0,
            'cash_register': self.cash_register,
            'payment_method': self.payment_method,
            'description': self.description,
            'movement_date': self.movement_date.isoformat() if self.movement_date else None,
            'movement_data': self.movement_data,
            'synced_at': self.synced_at.isoformat() if self.synced_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
