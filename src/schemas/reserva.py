"""
Schemas para reservas y QR dinámicos.
"""

from datetime import date, datetime, time

from pydantic import BaseModel

from models.models import EstadoReservaEnum


class ReservaBase(BaseModel):
    """Schema base de reserva"""

    id_local: int
    id_usuario: int
    fecha_reserva: date
    hora_reserva: time


class ReservaCreateSchema(ReservaBase):
    """Schema para crear reserva"""

    pass


class ReservaUpdateSchema(BaseModel):
    """Schema para actualizar reserva"""

    fecha_reserva: date | None = None
    hora_reserva: time | None = None
    estado: EstadoReservaEnum | None = None


class ReservaResponseSchema(ReservaBase):
    """Schema de respuesta de reserva"""

    id: int
    estado: EstadoReservaEnum
    creado_el: datetime | None = None
    expirado_el: datetime | None = None
    prioridad: str | None = None  # Calculada dinámicamente

    class Config:
        from_attributes = True


class ReservaSchema(ReservaBase):
    """Schema completo de reserva (legacy)"""

    id: int | None = None
    estado: EstadoReservaEnum
    creado_el: datetime | None = None
    expirado_el: datetime | None = None
    prioridad: str | None = None  # Calculada dinámicamente

    class Config:
        from_attributes = True


class QRDinamicoSchema(BaseModel):
    """Schema de QR dinámico"""

    id: int | None = None
    id_mesa: int
    id_pedido: int | None = None
    id_reserva: int | None = None
    id_usuario: int
    codigo: str
    expiracion: datetime
    activo: bool
    creado_el: datetime | None = None

    class Config:
        from_attributes = True
