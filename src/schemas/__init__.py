"""
Módulo de schemas Pydantic para validación de datos.

Los schemas están separados por dominio para mejor organización.
"""

# Schemas comunes
# Schemas de autenticación y usuarios
from .auth import (
    LoginSchema,
    RegisterSchema,
    RolSchema,
    UsuarioCreateSchema,
    UsuarioResponseSchema,
    UsuarioSchema,
    UsuarioUpdateSchema,
)
from .common import ErrorResponse, PaginatedResponse, PaginationParams, SuccessResponse

# Schemas de locales
from .local import LocalSchema, MesaSchema, OpinionSchema, ProductoSchema

# Schemas de pedidos
from .pedido import (
    CuentaSchema,
    EncomiendaSchema,
    EstadoPedidoSchema,
    PagoSchema,
    PedidoSchema,
)

# Schemas de reservas
from .reserva import (
    QRDinamicoSchema,
    ReservaCreateSchema,
    ReservaResponseSchema,
    ReservaSchema,
    ReservaUpdateSchema,
)

__all__ = [
    "CuentaSchema",
    "EncomiendaSchema",
    "ErrorResponse",
    "EstadoPedidoSchema",
    "LocalSchema",
    "LoginSchema",
    "MesaSchema",
    "OpinionSchema",
    "PaginatedResponse",
    "PaginationParams",
    "PagoSchema",
    "PedidoSchema",
    "ProductoSchema",
    "QRDinamicoSchema",
    "RegisterSchema",
    "ReservaCreateSchema",
    "ReservaResponseSchema",
    "ReservaSchema",
    "ReservaUpdateSchema",
    "RolSchema",
    "SuccessResponse",
    "UsuarioCreateSchema",
    "UsuarioResponseSchema",
    "UsuarioSchema",
    "UsuarioUpdateSchema",
]
