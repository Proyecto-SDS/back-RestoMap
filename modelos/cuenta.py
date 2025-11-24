from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from db.base import Base

class Cuenta(Base):

    __tablename__ = "cuenta"

    id = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False)
    id_producto = Column(Integer, ForeignKey("producto.id", ondelete="CASCADE"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    observaciones = Column(String(500), nullable=False)

    pedido = relationship("Pedido", back_populates="cuenta", lazy="joined")
    producto = relationship("Producto", back_populates="cuenta", lazy="joined")
    encomiendas_cuenta = relationship("EncomiendaCuenta", back_populates="cuenta", lazy="select")

    def __repr__(self):
       return f"<Cuenta id={self.id} pedido={self.id_pedido} producto={self.id_producto} cantidad={self.cantidad}" 
