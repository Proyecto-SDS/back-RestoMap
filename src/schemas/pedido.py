"""
Schemas para pedidos y gestión de órdenes.
"""

from datetime import datetime

from pydantic import BaseModel

from models.models import (
    EstadoEncomiendaEnum,
    EstadoPagoEnum,
    EstadoPedidoEnum,
    MetodoPagoEnum,
)


class PedidoSchema(BaseModel):
    """Schema de pedido"""

    id: int | None = None
    id_local: int
    id_mesa: int
    id_usuario: int
    id_qr: int
    creado_por: int
    estado: EstadoPedidoEnum
    total: int

    class Config:
        from_attributes = True


class CuentaSchema(BaseModel):
    """Schema de cuenta (items del pedido)"""

    id: int | None = None
    id_pedido: int
    id_producto: int
    creado_por: int
    cantidad: int
    observaciones: str | None = None
    creado_el: datetime | None = None

    class Config:
        from_attributes = True


class EstadoPedidoSchema(BaseModel):
    """Schema de cambio de estado de pedido"""

    id: int | None = None
    id_pedido: int
    estado: EstadoPedidoEnum
    creado_por: int
    creado_el: datetime | None = None
    nota: str | None = None

    class Config:
        from_attributes = True


class PagoSchema(BaseModel):
    """Schema de pago"""

    id: int | None = None
    id_pedido: int
    creado_por: int
    metodo: MetodoPagoEnum
    estado: EstadoPagoEnum
    monto: int

    class Config:
        from_attributes = True


class EncomiendaSchema(BaseModel):
    """Schema de encomienda (para llevar)"""

    id: int | None = None
    id_pedido: int
    estado: EstadoEncomiendaEnum
    creado_el: datetime | None = None

    class Config:
        from_attributes = True
