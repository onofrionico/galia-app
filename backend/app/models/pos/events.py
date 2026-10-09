from app.extensions import db


class PosSaleEvent(db.Model):
    __tablename__ = 'pos_sale_events'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=False, index=True)
    item_id = db.Column(db.Integer, nullable=True)  # sin FK: los ítems pendientes borrados conservan su evento
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_type = db.Column(db.String(30), nullable=False)
    payload = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, index=True)

    def to_dict(self):
        return {'id': self.id, 'sale_id': self.sale_id, 'item_id': self.item_id, 'user_id': self.user_id,
                'event_type': self.event_type, 'payload': self.payload, 'created_at': self.created_at.isoformat()}
