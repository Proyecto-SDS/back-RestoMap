"""
Excepciones HTTP personalizadas para API REST.

Proporciona excepciones específicas para códigos HTTP comunes.
"""

from .base import AppError


class HTTPError(AppError):
    """Excepción HTTP base"""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class BadRequestError(HTTPError):
    """Error 400 - Solicitud incorrecta"""

    def __init__(self, message: str = "Solicitud incorrecta"):
        super().__init__(message, status_code=400)


class UnauthorizedError(HTTPError):
    """Error 401 - No autenticado"""

    def __init__(self, message: str = "No autenticado"):
        super().__init__(message, status_code=401)


class ForbiddenError(HTTPError):
    """Error 403 - Acceso prohibido"""

    def __init__(self, message: str = "No tiene permisos para acceder a este recurso"):
        super().__init__(message, status_code=403)


class NotFoundError(HTTPError):
    """Error 404 - Recurso no encontrado"""

    def __init__(
        self, message: str = "Recurso no encontrado", resource: str | None = None
    ):
        super().__init__(message, status_code=404)
        if resource:
            self.details["resource"] = resource


class ConflictError(HTTPError):
    """Error 409 - Conflicto (ej: recurso duplicado)"""

    def __init__(self, message: str = "El recurso ya existe"):
        super().__init__(message, status_code=409)


class UnprocessableEntityError(HTTPError):
    """Error 422 - Entidad no procesable"""

    def __init__(
        self,
        message: str = "No se puede procesar la entidad",
        errors: list | None = None,
    ):
        super().__init__(message, status_code=422)
        if errors:
            self.details["errors"] = errors


class TooManyRequestsError(HTTPError):
    """Error 429 - Demasiadas solicitudes"""

    def __init__(self, message: str = "Demasiadas solicitudes. Intente más tarde"):
        super().__init__(message, status_code=429)


class InternalServerError(HTTPError):
    """Error 500 - Error interno del servidor"""

    def __init__(self, message: str = "Error interno del servidor"):
        super().__init__(message, status_code=500)
