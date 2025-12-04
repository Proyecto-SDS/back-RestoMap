"""
Schemas comunes y base para todo el sistema.
"""

from pydantic import BaseModel


class SuccessResponse(BaseModel):
    """Respuesta exitosa genérica"""

    success: bool = True
    message: str
    data: dict | list | None = None


class ErrorResponse(BaseModel):
    """Respuesta de error genérica"""

    success: bool = False
    error: str
    details: dict | None = None


class PaginationParams(BaseModel):
    """Parámetros de paginación"""

    page: int = 1
    per_page: int = 20
    offset: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        # Calcular offset automáticamente
        self.offset = (self.page - 1) * self.per_page


class PaginatedResponse(BaseModel):
    """Respuesta paginada genérica"""

    success: bool = True
    data: list
    pagination: dict

    class Config:
        from_attributes = True
