"""
Excepciones base del sistema RestoMap.

Define las excepciones fundamentales que heredan otras excepciones específicas.
"""


class AppError(Exception):
    """Excepción base de la aplicación"""

    def __init__(
        self, message: str = "Error de aplicación", details: dict | None = None
    ):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppError):
    """Error de validación de datos"""

    def __init__(self, message: str = "Error de validación", field: str | None = None):
        super().__init__(message)
        self.field = field
        if field:
            self.details["field"] = field


class BusinessLogicError(AppError):
    """Error en lógica de negocio"""

    def __init__(self, message: str = "Error de lógica de negocio"):
        super().__init__(message)


class DatabaseError(AppError):
    """Error de base de datos"""

    def __init__(self, message: str = "Error de base de datos"):
        super().__init__(message)
