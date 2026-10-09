class PosError(Exception):
    """Error de negocio del POS. Las rutas lo traducen a {'error': message, **extra} con `status`."""

    def __init__(self, message, status=409, **extra):
        super().__init__(message)
        self.message = message
        self.status = status
        self.extra = extra


def bad_request(message, **extra):
    return PosError(message, 400, **extra)


def forbidden(message):
    return PosError(message, 403)


def not_found(message):
    return PosError(message, 404)
