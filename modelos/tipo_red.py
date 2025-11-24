from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.base import Base

class TipoRed(Base):

    __tablename__= "tipo_red"

    id = Column(Integer, primary_key=True, index=False)
    nombre = Column(String(100), nullable=False)

    redes = relationship("Redes", back_populates="tipo_red", lazy="select")

    def __repr__(self):
        return f"<Tipo_red id={self.id}, nombre={self.nombre}"