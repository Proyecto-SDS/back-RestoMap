"""
Schemas para reservas y QR dinamicos.
"""

from datetime import date, datetime, time

from pydantic import BaseModel, Field, field_validator

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


class ReservaCreateInputSchema(BaseModel):
    """Schema para crear reserva desde el frontend"""

    local_id: int = Field(..., gt=0, alias="localId")
    mesa_id: int = Field(..., gt=0, alias="mesaId")
    fecha: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    hora: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    numero_personas: int = Field(default=2, ge=1, le=20, alias="numeroPersonas")

    class Config:
        populate_by_name = True

    # pyrefly: ignore  # bad-argument-type
    @field_validator("fecha")
    @classmethod
    def validar_fecha(cls, v: str) -> str:
        try:
            fecha_parsed = datetime.strptime(v, "%Y-%m-%d").date()
            if fecha_parsed < date.today():
                msg = "La fecha debe ser futura"
                raise ValueError(msg)
        except ValueError as e:
            if "La fecha debe ser futura" in str(e):
                raise
            msg = "Formato de fecha invalido. Use: YYYY-MM-DD"
            raise ValueError(msg) from e
        return v

    # pyrefly: ignore  # bad-argument-type
    @field_validator("hora")
    @classmethod
    def validar_hora(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError as e:
            msg = "Formato de hora invalido. Use: HH:MM"
            raise ValueError(msg) from e
        return v


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
    prioridad: str | None = None  # Calculada dinamicamente

    class Config:
        from_attributes = True


class ReservaSchema(ReservaBase):
    """Schema completo de reserva (legacy)"""

    id: int | None = None
    estado: EstadoReservaEnum
    creado_el: datetime | None = None
    expirado_el: datetime | None = None
    prioridad: str | None = None  # Calculada dinamicamente

    class Config:
        from_attributes = True


class QRDinamicoSchema(BaseModel):
    """Schema de QR dinamico"""

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
