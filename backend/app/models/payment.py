# backend/app/models/payment.py
from datetime import datetime
from app.extensions import db

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    method = db.Column(db.String(50), nullable=False)  # 'efectivo', 'tarjeta', 'transferencia', 'otro'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    sale = db.relationship('Sale', backref='payments')
    user = db.relationship('User', backref='payments')

    def to_dict(self):
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'amount': float(self.amount),
            'method': self.method,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
        }
