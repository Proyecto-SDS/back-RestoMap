from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.base import Base

class TipoFoto(Base):

    __tablename__= "tipo_foto"

    id = Column(Integer, primary_key=True, index=False)
    nombre = Column(String(100), nullable=False)

    foto = relationship("Foto", back_populates="tipo_red", lazy="select")

    def __repr__(self):
        return f"<Tipo_foto id={self.id}, nombre={self.nombre}"