from datetime import datetime
from app.extensions import db

class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    from_currency = db.Column(db.String(10), nullable=False)
    to_currency = db.Column(db.String(10), nullable=False)
    rate = db.Column(db.Numeric(12, 6), nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    source = db.Column(db.String(20), nullable=False, default='manual')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])
    
    __table_args__ = (
        db.UniqueConstraint('from_currency', 'to_currency', 'effective_date', name='uq_exchange_rate_date'),
        db.Index('idx_exchange_rates_currencies', 'from_currency', 'to_currency'),
        db.Index('idx_exchange_rates_effective_date', 'effective_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'from_currency': self.from_currency,
            'to_currency': self.to_currency,
            'rate': float(self.rate) if self.rate else 0,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by_user_id': self.created_by_user_id
        }
    
    @staticmethod
    def get_rate_for_date(from_currency, to_currency, date):
        """Get exchange rate for a specific date (or most recent before that date)"""
        rate = ExchangeRate.query.filter(
            ExchangeRate.from_currency == from_currency,
            ExchangeRate.to_currency == to_currency,
            ExchangeRate.effective_date <= date
        ).order_by(ExchangeRate.effective_date.desc()).first()
        
        return float(rate.rate) if rate else None
    
    def __repr__(self):
        return f'<ExchangeRate {self.from_currency}/{self.to_currency} = {self.rate} on {self.effective_date}>'
