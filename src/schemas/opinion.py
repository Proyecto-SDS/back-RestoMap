"""
Schemas para opiniones.
"""

from pydantic import BaseModel, Field, field_validator


class OpinionCreateSchema(BaseModel):
    """Schema para crear opinion"""

    local_id: int = Field(..., gt=0, alias="localId")
    puntuacion: float = Field(..., ge=1, le=5)
    comentario: str = Field(..., min_length=10, max_length=500)

    class Config:
        populate_by_name = True

    # pyrefly: ignore  # bad-argument-type
    @field_validator("puntuacion")
    @classmethod
    def validar_puntuacion(cls, v: float) -> float:
        # Redondear a 1 decimal
        return round(v, 1)
