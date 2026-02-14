from datetime import datetime
from app.extensions import db

class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255))
    expense_type = db.Column(db.String(20), nullable=False, default='indirecto')  # 'directo' o 'indirecto'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    expenses = db.relationship('Expense', backref='category_rel', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'expense_type': self.expense_type,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.Integer, unique=True, nullable=True, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    fecha_vencimiento = db.Column(db.Date, nullable=True)
    proveedor = db.Column(db.String(200))
    categoria = db.Column(db.String(100))
    subcategoria = db.Column(db.String(100))
    comentario = db.Column(db.Text)
    estado_pago = db.Column(db.String(50), default='Pendiente')
    importe = db.Column(db.Numeric(12, 2), nullable=False)
    de_caja = db.Column(db.Boolean, default=False)
    caja = db.Column(db.String(100))
    medio_pago = db.Column(db.String(100))
    numero_fiscal = db.Column(db.String(100))
    tipo_comprobante = db.Column(db.String(100))
    numero_comprobante = db.Column(db.String(100))
    creado_por = db.Column(db.String(100))
    cancelado = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=True)
    
    __table_args__ = (
        db.Index('idx_expenses_fecha', 'fecha'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'external_id': self.external_id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'fecha_vencimiento': self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None,
            'proveedor': self.proveedor,
            'categoria': self.categoria,
            'subcategoria': self.subcategoria,
            'comentario': self.comentario,
            'estado_pago': self.estado_pago,
            'importe': float(self.importe) if self.importe else 0,
            'de_caja': self.de_caja,
            'caja': self.caja,
            'medio_pago': self.medio_pago,
            'numero_fiscal': self.numero_fiscal,
            'tipo_comprobante': self.tipo_comprobante,
            'numero_comprobante': self.numero_comprobante,
            'creado_por': self.creado_por,
            'cancelado': self.cancelado,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def parse_date(date_str):
        """Parse date from CSV format (DD/MM/YYYY)"""
        if not date_str or not date_str.strip():
            return None
        try:
            return datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
        except ValueError:
            try:
                return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
            except ValueError:
                return None
    
    @staticmethod
    def parse_bool(value):
        """Parse boolean from CSV (Sí/No)"""
        if not value:
            return False
        return value.strip().lower() in ['sí', 'si', 'yes', 'true', '1']
    
    @staticmethod
    def parse_decimal(value):
        """Parse decimal from CSV"""
        if not value or not str(value).strip():
            return 0
        try:
            cleaned = str(value).replace(',', '.').strip()
            return float(cleaned)
        except (ValueError, TypeError):
            return 0
    
    @classmethod
    def from_csv_row(cls, row):
        """Create an Expense instance from a CSV row"""
        external_id = row.get('Id', '').strip()
        
        return cls(
            external_id=int(external_id) if external_id else None,
            fecha=cls.parse_date(row.get('Fecha', '')),
            fecha_vencimiento=cls.parse_date(row.get('Fecha de vencimiento', '')),
            proveedor=row.get('Proveedor', '').strip() or None,
            categoria=row.get('Categoría', '').strip() or None,
            subcategoria=row.get('Subcategoría', '').strip() or None,
            comentario=row.get('Comentario', '').strip() or None,
            estado_pago=row.get('Estado del pago', '').strip() or 'Pendiente',
            importe=cls.parse_decimal(row.get('Importe', 0)),
            de_caja=cls.parse_bool(row.get('De Caja', '')),
            caja=row.get('Caja', '').strip() or None,
            medio_pago=row.get('Medio de pago', '').strip() or None,
            numero_fiscal=row.get('Número Fiscal', '').strip() or None,
            tipo_comprobante=row.get('Tipo de comprobante', '').strip() or None,
            numero_comprobante=row.get('N° de comprobante', '').strip() or None,
            creado_por=row.get('Creado por', '').strip() or None,
            cancelado=cls.parse_bool(row.get('Cancelado', ''))
        )
