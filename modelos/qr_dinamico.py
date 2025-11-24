from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class QRDinamico(Base):

    __tablename__= "qr_dinamico"

    id = Column(Integer, primary_key=True, index=False)
    id_mesa = Column(Integer, ForeignKey("mesa.id", ondelete="CASCADE"), nullable=False)
    id_pedido = Column(Integer, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False)
    codigo = Column(String, nullable=False)
    expiracion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    mesa = relationship("Mesa", back_populates="qr_dinamico", lazy="joined")
    pedido = relationship("Pedido", back_populates="qr_dinamico", lazy="joined")

    def __repr__(self):
        return f"<QR_Dinamico id{self.id} mesa={self.id_mesa} pedido={self.id_pedido} codigo={self.codigo} expiracion={self.expiracion} actico={self.activo}"