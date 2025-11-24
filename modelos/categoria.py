from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.base import Base


class Categoria(Base):

    __tablename__ = "categoria"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)

    # Relaciones
    producto = relationship("Producto", back_populates="categoria", lazy="selectin")
    foto = relationship("Foto", back_populates="categoria", lazy="selectin")

    def __repr__(self):
        return f"<Categoria id={self.id} nombre={self.nombre}>"