# Base general para todos los schemas.

from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class TimestampModel(BaseModel):
    
    creado_el: Optional[datetime] = None
    actualizado_el: Optional[datetime] = None
    eliminado_el: Optional[datetime] = None

    class Config:
        orm_mode = True