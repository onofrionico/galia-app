from app.services.pos.errors import PosError


class LoyaltyError(PosError):
    """Error de negocio de fidelización. Hereda de PosError para que las rutas del POS lo traduzcan igual."""

    def __init__(self, message, status=400, **extra):
        super().__init__(message, status, **extra)
