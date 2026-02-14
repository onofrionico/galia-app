from datetime import datetime
from app.extensions import db

class Sale(db.Model):
    """
    Sale model matching CSV structure:
    Id, Fecha, Creación, Cerrada, Caja, Estado, Cliente, Mesa, Sala, Personas,
    Camarero / Repartidor, Medio de Pago, Total, Fiscal, Tipo de Venta, Comentario, Origen, Id. Origen
    """
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.Integer, unique=True, nullable=True, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    creacion = db.Column(db.DateTime, nullable=False)
    cerrada = db.Column(db.DateTime, nullable=True)
    caja = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(50), nullable=False, default='En curso')
    cliente = db.Column(db.String(200), nullable=True)
    mesa = db.Column(db.String(20), nullable=True)
    sala = db.Column(db.String(100), nullable=True)
    personas = db.Column(db.Integer, nullable=True)
    camarero = db.Column(db.String(200), nullable=True)
    medio_pago = db.Column(db.String(100), nullable=True)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    fiscal = db.Column(db.Boolean, nullable=False, default=False)
    tipo_venta = db.Column(db.String(50), nullable=False, default='Local')
    comentario = db.Column(db.Text, nullable=True)
    origen = db.Column(db.String(100), nullable=True)
    id_origen = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.Index('idx_sales_fecha', 'fecha'),
        db.Index('idx_sales_estado', 'estado'),
        db.Index('idx_sales_tipo_venta', 'tipo_venta'),
        db.Index('idx_sales_origen', 'origen'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'external_id': self.external_id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'creacion': self.creacion.isoformat() if self.creacion else None,
            'cerrada': self.cerrada.isoformat() if self.cerrada else None,
            'caja': self.caja,
            'estado': self.estado,
            'cliente': self.cliente,
            'mesa': self.mesa,
            'sala': self.sala,
            'personas': self.personas,
            'camarero': self.camarero,
            'medio_pago': self.medio_pago,
            'total': float(self.total) if self.total else 0,
            'fiscal': self.fiscal,
            'tipo_venta': self.tipo_venta,
            'comentario': self.comentario,
            'origen': self.origen,
            'id_origen': self.id_origen,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def from_csv_row(row):
        """Create a Sale instance from a CSV row dict"""
        from datetime import datetime as dt
        
        def parse_date(date_str):
            if not date_str or date_str.strip() == '':
                return None
            try:
                return dt.strptime(date_str.strip(), '%d/%m/%Y').date()
            except ValueError:
                return None
        
        def parse_datetime(datetime_str):
            if not datetime_str or datetime_str.strip() == '':
                return None
            try:
                return dt.strptime(datetime_str.strip(), '%d/%m/%Y %H:%M:%S')
            except ValueError:
                try:
                    return dt.strptime(datetime_str.strip(), '%d/%m/%Y')
                except ValueError:
                    return None
        
        def parse_int(val):
            if not val or val.strip() == '':
                return None
            try:
                return int(val.strip())
            except ValueError:
                return None
        
        def parse_decimal(val):
            if not val or val.strip() == '':
                return 0
            try:
                return float(val.strip().replace(',', '.'))
            except ValueError:
                return 0
        
        def parse_bool(val):
            if not val:
                return False
            return val.strip().lower() in ('si', 'sí', 'yes', 'true', '1')
        
        return Sale(
            external_id=parse_int(row.get('Id')),
            fecha=parse_date(row.get('Fecha')),
            creacion=parse_datetime(row.get('Creación')) or dt.now(),
            cerrada=parse_datetime(row.get('Cerrada')),
            caja=row.get('Caja', '').strip() or None,
            estado=row.get('Estado', 'En curso').strip() or 'En curso',
            cliente=row.get('Cliente', '').strip() or None,
            mesa=row.get('Mesa', '').strip() or None,
            sala=row.get('Sala', '').strip() or None,
            personas=parse_int(row.get('Personas')),
            camarero=row.get('Camarero / Repartidor', '').strip() or None,
            medio_pago=row.get('Medio de Pago', '').strip() or None,
            total=parse_decimal(row.get('Total')),
            fiscal=parse_bool(row.get('Fiscal')),
            tipo_venta=row.get('Tipo de Venta', 'Local').strip() or 'Local',
            comentario=row.get('Comentario', '').strip() or None,
            origen=row.get('Origen', '').strip() or None,
            id_origen=row.get('Id. Origen', '').strip() or None
        )
