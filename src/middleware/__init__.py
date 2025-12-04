"""
Módulo de middleware personalizado para el sistema RestoMap.
"""

from .error_handler import register_error_handlers
from .logging import setup_request_logging
from .request_id import setup_request_id


def register_middleware(app):
    """
    Registra todo el middleware en la aplicación Flask.

    Args:
        app: Instancia de Flask

    Orden de registro:
    1. Request ID (primero para tener ID disponible en otros middleware)
    2. Logging (segundo para loggear con Request ID)
    3. Error handlers (último para capturar todos los errores)
    """
    setup_request_id(app)
    setup_request_logging(app)
    register_error_handlers(app)


__all__ = [
    "register_error_handlers",
    "register_middleware",
    "setup_request_id",
    "setup_request_logging",
]
