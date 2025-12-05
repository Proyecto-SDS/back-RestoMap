"""
Schemas para favoritos.
"""

from pydantic import BaseModel, Field


class FavoritoCreateSchema(BaseModel):
    """Schema para agregar favorito"""

    local_id: int = Field(..., gt=0, alias="localId")

    class Config:
        populate_by_name = True
