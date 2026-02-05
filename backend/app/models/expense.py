from datetime import datetime
from app.extensions import db

class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    expenses = db.relationship('Expense', backref='category', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active
        }

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    supplier = db.Column(db.String(200))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    creator = db.relationship('User', backref='expenses_created')
    
    __table_args__ = (
        db.Index('idx_expenses_date', 'expense_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'expense_date': self.expense_date.isoformat(),
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'description': self.description,
            'supplier': self.supplier,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }
