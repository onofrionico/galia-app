from datetime import datetime
from app.extensions import db


class ReportGoal(db.Model):
    """
    Modelo para almacenar metas/alcanzables configurables.
    Permite definir objetivos de ventas, rentabilidad, productividad y gastos.
    """
    __tablename__ = 'report_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Tipo de meta: ventas, rentabilidad, productividad, gastos_directos, gastos_indirectos, costo_laboral
    goal_type = db.Column(db.String(30), nullable=False)
    
    # Período: diario, semanal, mensual, trimestral, anual
    period_type = db.Column(db.String(20), nullable=False, default='mensual')
    
    # Valor objetivo
    target_value = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Unidad: monto, porcentaje, ratio
    target_unit = db.Column(db.String(20), nullable=False, default='monto')
    
    # Tipo de comparación: mayor_o_igual (para ventas), menor_o_igual (para gastos)
    comparison_type = db.Column(db.String(20), nullable=False, default='mayor_o_igual')
    
    # Vigencia
    valid_from = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    valid_to = db.Column(db.Date, nullable=True)  # NULL = vigente
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    __table_args__ = (
        db.Index('idx_report_goals_active', 'is_active', 'goal_type'),
        db.Index('idx_report_goals_period', 'valid_from', 'valid_to'),
    )
    
    # Constantes para tipos de meta
    GOAL_TYPES = ['ventas', 'rentabilidad', 'productividad', 'gastos_directos', 'gastos_indirectos', 'costo_laboral']
    PERIOD_TYPES = ['diario', 'semanal', 'mensual', 'trimestral', 'anual']
    TARGET_UNITS = ['monto', 'porcentaje', 'ratio']
    COMPARISON_TYPES = ['mayor_o_igual', 'menor_o_igual']
    
    def to_dict(self):
        return {
            'id': self.id,
            'goal_type': self.goal_type,
            'period_type': self.period_type,
            'target_value': float(self.target_value) if self.target_value else 0,
            'target_unit': self.target_unit,
            'comparison_type': self.comparison_type,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_to': self.valid_to.isoformat() if self.valid_to else None,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by_id': self.created_by_id
        }
    
    @classmethod
    def get_active_goals(cls):
        """Obtener todas las metas activas y vigentes"""
        from datetime import date
        today = date.today()
        return cls.query.filter(
            cls.is_active == True,
            cls.valid_from <= today,
            db.or_(cls.valid_to.is_(None), cls.valid_to >= today)
        ).all()
    
    @classmethod
    def get_goal_by_type(cls, goal_type):
        """Obtener la meta activa de un tipo específico"""
        from datetime import date
        today = date.today()
        return cls.query.filter(
            cls.is_active == True,
            cls.goal_type == goal_type,
            cls.valid_from <= today,
            db.or_(cls.valid_to.is_(None), cls.valid_to >= today)
        ).first()


class DashboardSnapshot(db.Model):
    """
    Cache de métricas del dashboard para mejorar performance.
    Almacena snapshots de métricas calculadas por día.
    """
    __tablename__ = 'dashboard_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    snapshot_date = db.Column(db.Date, nullable=False)
    period_type = db.Column(db.String(20), nullable=False)  # diario, semanal, mensual
    
    # Métricas almacenadas como JSON
    metrics = db.Column(db.JSON, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('snapshot_date', 'period_type', name='uq_snapshot_date_period'),
        db.Index('idx_dashboard_snapshots_date', 'snapshot_date', 'period_type'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'period_type': self.period_type,
            'metrics': self.metrics,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
