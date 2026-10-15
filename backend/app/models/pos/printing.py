from app.extensions import db

PRINT_JOB_KINDS = ('order', 'void', 'bill', 'receipt', 'test', 'invoice')
PRINT_JOB_STATUSES = ('pending', 'printing', 'printed', 'failed')
PRINTER_CONNECTIONS = ('network', 'usb')
PAPER_WIDTHS = (58, 80)


class PrintStation(db.Model):
    __tablename__ = 'print_stations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False, unique=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'position': self.position, 'is_active': self.is_active}


class Printer(db.Model):
    __tablename__ = 'printers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False, unique=True)
    connection = db.Column(db.String(10), nullable=False)
    host = db.Column(db.String(100), nullable=True)
    port = db.Column(db.Integer, nullable=False, default=9100)
    os_name = db.Column(db.String(120), nullable=True)
    paper_width = db.Column(db.Integer, nullable=False, default=80)
    print_point = db.Column(db.String(60), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey('print_stations.id'), nullable=True)
    is_cashier = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    station = db.relationship('PrintStation')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'connection': self.connection, 'host': self.host,
                'port': self.port, 'os_name': self.os_name, 'paper_width': self.paper_width,
                'print_point': self.print_point, 'station_id': self.station_id,
                'station_name': self.station.name if self.station else None, 'is_cashier': self.is_cashier,
                'is_active': self.is_active}


class PrintJob(db.Model):
    __tablename__ = 'print_jobs'
    __table_args__ = (db.Index('ix_print_jobs_printer_status', 'printer_id', 'status', 'id'),)

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(10), nullable=False)
    printer_id = db.Column(db.Integer, db.ForeignKey('printers.id'), nullable=False, index=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=True, index=True)
    station_id = db.Column(db.Integer, db.ForeignKey('print_stations.id'), nullable=True)
    batch = db.Column(db.Integer, nullable=True)
    document = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(10), nullable=False, default='pending')
    attempts = db.Column(db.Integer, nullable=False, default=0)
    error = db.Column(db.String(255), nullable=True)
    claimed_by = db.Column(db.String(60), nullable=True)
    claimed_at = db.Column(db.DateTime, nullable=True)
    printed_at = db.Column(db.DateTime, nullable=True)
    failed_at = db.Column(db.DateTime, nullable=True)
    reprint_of = db.Column(db.Integer, db.ForeignKey('print_jobs.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    printer = db.relationship('Printer')
    sale = db.relationship('PosSale')
    station = db.relationship('PrintStation')


class QzSigningKey(db.Model):
    """Par de claves con el que Galia firma los pedidos a QZ Tray. Una sola fila (id=1), generada sola."""
    __tablename__ = 'qz_signing_keys'

    id = db.Column(db.Integer, primary_key=True)
    certificate = db.Column(db.Text, nullable=False)
    private_key = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)


class PrintPoint(db.Model):
    """Punto de impresión (una PC con la página /pos/impresion). Se crea al configurar impresoras."""
    __tablename__ = 'print_points'

    name = db.Column(db.String(60), primary_key=True)
    last_seen_at = db.Column(db.DateTime, nullable=True)
