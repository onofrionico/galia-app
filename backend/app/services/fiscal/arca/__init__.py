"""Acceso a ARCA. `get_gateway` devuelve el cliente real (WSAA + WSFEv1) o FakeArca para desarrollo."""
import os

from app.extensions import db


class ArcaUnavailable(Exception):
    """ARCA no respondió (red, timeout, SOAP Fault)."""


class ArcaRejected(Exception):
    """ARCA respondió con errores (no con un comprobante rechazado)."""

    def __init__(self, errors):
        super().__init__('; '.join(f"{e['code']}: {e['msg']}" for e in errors))
        self.errors = errors


def fake_enabled():
    """FakeArca solo con FISCAL_FAKE_ARCA=1 y base SQLite: con PostgreSQL (producción) nunca."""
    return os.getenv('FISCAL_FAKE_ARCA') == '1' and db.engine.dialect.name == 'sqlite'


def get_gateway(settings):
    if fake_enabled():
        from app.services.fiscal.arca.fake import FakeArca
        # Para el preview: FISCAL_FAKE_ARCA_MODE=timeout|reject|timeout_after_issue simula fallas de ARCA.
        FakeArca.mode = os.getenv('FISCAL_FAKE_ARCA_MODE', 'approve')
        return FakeArca()
    from app.services.fiscal.arca import wsaa, wsfe
    token, sign = wsaa.credentials(settings)
    return wsfe.WsfeClient(settings.environment, settings.cuit, token, sign)
