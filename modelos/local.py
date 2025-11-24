from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from db.base import Base

class Local(Base):

    __tablename__= "local"

    id = Column(Integer, primary_key=True, index=True)
    id_direccion = Column(Integer, ForeignKey("direccion.id", ondelete="CASCADE"), nullable=False)
    id_tipo_local = Column(Integer, ForeignKey("tipo_local.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String(200), nullable=False)
    telefono = Column(Integer, nullable=False)
    correo = Column(String(50), nullable=False)

    horarios = relationship("Horario", back_populates="local", lazy="select")
    direccion = relationship("Direccion", back_populates="local", lazy="joined")
    producto = relationship("Producto", back_populates="local", lazy="select")
    tipo_local = relationship("TipoLocal", back_populates="local", lazy="joined")
    redes = relationship("Redes", back_populates="local", lazy="joined")
    foto = relationship("Foto", back_populates="local", lazy="joined")

    def __repr__(self):
        return f"<Local id={self.id} direccion={self.id_direccion} nombre={self.nombre} tipo_local={self.id_tipo_local} telefono={self.telefono} correo={self.correo}>"
