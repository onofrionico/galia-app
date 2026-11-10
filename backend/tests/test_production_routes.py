"""Endpoints del pronóstico de producción, sus turnos y los componentes de productos."""
from app.extensions import db
from app.models import ProductionSettings
from pos_helpers import pos_app  # noqa: F401


def test_settings_get_creates_defaults(pos_app):
    settings = ProductionSettings.get()
    db.session.commit()
    assert settings.comparable_weeks == 4 and settings.holiday_window_months == 12
    ProductionSettings.get()
    db.session.commit()
    assert ProductionSettings.query.count() == 1
