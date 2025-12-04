"""
Schemas para locales y gestión de restaurantes.
"""

from datetime import datetime

from pydantic import BaseModel

from models.models import EstadoMesaEnum


class LocalSchema(BaseModel):
    """Schema de local"""

    id: int | None = None
    nombre: str
    telefono: int
    correo: str
    id_direccion: int
    id_tipo_local: int

    class Config:
        from_attributes = True


class MesaSchema(BaseModel):
    """Schema de mesa"""

    id: int | None = None
    id_local: int
    nombre: str
    descripcion: str | None = None
    capacidad: int
    estado: EstadoMesaEnum

    class Config:
        from_attributes = True


class ProductoSchema(BaseModel):
    """Schema de producto"""

    id: int | None = None
    nombre: str
    descripcion: str | None = None
    precio: int
    estado: str  # Se puede importar EstadoProductoEnum si se necesita
    id_local: int
    id_categoria: int | None = None

    class Config:
        from_attributes = True


class OpinionSchema(BaseModel):
    """Schema de opinión"""

    id: int | None = None
    id_usuario: int
    id_local: int
    puntuacion: float
    comentario: str
    creado_el: datetime | None = None
    eliminado_el: datetime | None = None

    class Config:
        from_attributes = True
