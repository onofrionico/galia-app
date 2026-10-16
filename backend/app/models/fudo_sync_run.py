from datetime import datetime

from app.extensions import db


class FudoSyncRun(db.Model):
    """Una corrida de sincronización con Fudo (por ahora solo kind='expenses')."""
    __tablename__ = 'fudo_sync_runs'
    __table_args__ = (db.Index('ix_fudo_sync_runs_kind_started_at', 'kind', 'started_at'),)

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(10), nullable=False)  # running | ok | error
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    params = db.Column(db.JSON, nullable=True)
    stats = db.Column(db.JSON, nullable=True)
    error = db.Column(db.Text, nullable=True)
    triggered_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'kind': self.kind,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'params': self.params,
            'stats': self.stats,
            'error': self.error,
            'triggered_by': self.triggered_by,
        }
