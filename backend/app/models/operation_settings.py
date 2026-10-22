"""Interruptores del corte con Fudo y control de la importación de su historia de ventas."""
from app.extensions import db

SETTINGS_ID = 1


class OperationSettings(db.Model):
    """Una sola fila: catálogo en Galia, Fudo apagado y modo práctica."""
    __tablename__ = 'operation_settings'

    id = db.Column(db.Integer, primary_key=True)
    catalog_in_galia = db.Column(db.Boolean, nullable=False, default=False)
    fudo_off = db.Column(db.Boolean, nullable=False, default=False)
    practice_mode = db.Column(db.Boolean, nullable=False, default=False)
    updated_at = db.Column(db.DateTime, nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {'catalog_in_galia': self.catalog_in_galia, 'fudo_off': self.fudo_off,
                'practice_mode': self.practice_mode}


class FudoImportMonth(db.Model):
    """Control por mes de la importación: lo que trajo Fudo contra lo que quedó en Galia."""
    __tablename__ = 'fudo_import_months'

    month = db.Column(db.Date, primary_key=True)  # día 1
    status = db.Column(db.String(10), nullable=False, default='pending')  # pending | done | error
    fudo_count = db.Column(db.Integer, nullable=False, default=0)
    fudo_total = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    galia_count = db.Column(db.Integer, nullable=False, default=0)
    galia_total = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    changed = db.Column(db.Integer, nullable=False, default=0)
    errors = db.Column(db.JSON, nullable=True)
    imported_at = db.Column(db.DateTime, nullable=True)
    run_id = db.Column(db.Integer, db.ForeignKey('fudo_sync_runs.id'), nullable=True)

    @property
    def matches(self):
        return self.fudo_count == self.galia_count and self.fudo_total == self.galia_total

    def to_dict(self):
        return {'month': self.month.strftime('%Y-%m'), 'status': self.status, 'fudo_count': self.fudo_count,
                'fudo_total': f'{self.fudo_total:.2f}', 'galia_count': self.galia_count,
                'galia_total': f'{self.galia_total:.2f}', 'matches': self.matches, 'changed': self.changed,
                'errors': self.errors or [],
                'imported_at': self.imported_at.isoformat() if self.imported_at else None}
