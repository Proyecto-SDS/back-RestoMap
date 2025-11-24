from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from db.base import Base
import enum

class ProductoEnum(enum.Enum):
    DISPONIBLE = 'disponible'
    AGOTADO = 'agotado'
    INACTIVO = 'inactivo'

class Producto(Base):

    __tablename__ = "producto"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True)
    id_categoria = Column(Integer, ForeignKey("categoria.id", ondelete="SET NULL"), nullable=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(500), nullable=True)
    estado = Column(Enum(ProductoEnum, name="estado_producto_enum"), nullable=False)
    precio = Column(Integer, nullable=False)

    # Relaciones
    local = relationship("Local", back_populates="productos", lazy="joined")
    categoria = relationship("Categoria", back_populates="productos", lazy="joined")
    cuentas = relationship("Cuenta", back_populates="producto", lazy="select")
    foto = relationship("Foto", back_populates="producto", lazy="joined")

    def __repr__(self):
        return f"<Producto id={self.id} nombre={self.nombre} estado={self.estado} precio={self.precio}>"
