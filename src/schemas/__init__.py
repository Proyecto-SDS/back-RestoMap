"""
Modulo de schemas Pydantic para validacion de datos.

Los schemas estan separados por dominio para mejor organizacion.
"""

# Schemas comunes
# Schemas de autenticacion y usuarios
from .auth import (
    LoginSchema,
    ProfileUpdateSchema,
    RegisterSchema,
    RolSchema,
    UsuarioCreateSchema,
    UsuarioResponseSchema,
    UsuarioSchema,
    UsuarioUpdateSchema,
)
from .common import ErrorResponse, PaginatedResponse, PaginationParams, SuccessResponse

# Schemas de favoritos
from .favorito import FavoritoCreateSchema

# Schemas de locales
from .local import LocalSchema, MesaSchema, OpinionSchema, ProductoSchema

# Schemas de opiniones
from .opinion import OpinionCreateSchema

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
    ReservaCreateInputSchema,
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
    "FavoritoCreateSchema",
    "LocalSchema",
    "LoginSchema",
    "MesaSchema",
    "OpinionCreateSchema",
    "OpinionSchema",
    "PaginatedResponse",
    "PaginationParams",
    "PagoSchema",
    "PedidoSchema",
    "ProductoSchema",
    "ProfileUpdateSchema",
    "QRDinamicoSchema",
    "RegisterSchema",
    "ReservaCreateInputSchema",
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
