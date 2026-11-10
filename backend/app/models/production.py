"""Pronóstico de producción: turnos del día, configuración y componentes de productos (combos)."""
from datetime import datetime

from app.extensions import db

PRODUCTION_SETTINGS_ID = 1


class SalesDayPart(db.Model):
    """Turno del día para agrupar ventas (Desayuno, Almuerzo, Merienda). Intervalo [inicio, fin)."""
    __tablename__ = 'sales_day_parts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    updated_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'start': self.start_time.strftime('%H:%M'),
                'end': self.end_time.strftime('%H:%M'), 'position': self.position, 'is_active': self.is_active}


class ProductionSettings(db.Model):
    """Una sola fila: cuántas semanas y meses de feriados se comparan."""
    __tablename__ = 'production_settings'

    id = db.Column(db.Integer, primary_key=True)
    comparable_weeks = db.Column(db.Integer, nullable=False, default=4)
    holiday_window_months = db.Column(db.Integer, nullable=False, default=12)
    updated_at = db.Column(db.DateTime, nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    @classmethod
    def get(cls):
        """La fila única; si falta, la crea con los valores por defecto (sin commit)."""
        settings = db.session.get(cls, PRODUCTION_SETTINGS_ID)
        if settings is None:
            settings = cls(id=PRODUCTION_SETTINGS_ID, comparable_weeks=4, holiday_window_months=12)
            db.session.add(settings)
            db.session.flush()
        return settings


class ProductComponent(db.Model):
    """Una variante (el combo) trae `quantity` unidades de otra variante (el componente)."""
    __tablename__ = 'product_components'
    __table_args__ = (db.UniqueConstraint('variant_id', 'component_variant_id', name='uq_product_component'),)

    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False, index=True)
    component_variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    updated_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    component_variant = db.relationship('ProductVariant', foreign_keys=[component_variant_id])
