from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base


class Foto(Base):
    __tablename__ = "foto"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=True, index=True)
    id_producto = Column(Integer, ForeignKey("producto.id", ondelete="SET NULL"), nullable=True, index=True)
    id_categoria = Column(Integer, ForeignKey("categoria.id", ondelete="SET NULL"), nullable=True, index=True)
    id_tipo_foto = Column(Integer, ForeignKey("tipo_foto.id", ondelete="SET NULL"), nullable=True, index=True)
    ruta = Column(Text, nullable=False)

    # Relaciones
    local = relationship("Local", back_populates="foto", lazy="joined")
    producto = relationship("Producto", back_populates="foto", lazy="joined")
    categoria = relationship("Categoria", back_populates="foto", lazy="joined")
    tipo_foto = relationship("TipoFoto", back_populates="foto", lazy="joined")
    redes = relationship("Redes", back_populates="foto", lazy="select")

    def __repr__(self):
        return (
            f"<Foto id={self.id} ruta={self.ruta} "
            f"id_local={self.id_local} id_producto={self.id_producto} "
            f"id_categoria={self.id_categoria} id_tipo_foto={self.id_tipo_foto}>"
        )
