from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base
import enum

class EncomiendaEnum(enum.Enum):
    PENDIENTE = 'pendiente'
    EN_PREPARACION = 'en_preparacion'
    LISTA = 'lista'
    ENTREGADA = 'entregada'
    CANCELADA = 'cancelada'

class Encomienda(Base):

    __tablename__ = "encomienda"

    id = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False, index=True)
    estado = Column(Enum(EncomiendaEnum, name="estado_encomienda_enum"), nullable=False)
    creado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    pedido = relationship("Pedido", back_populates="encomiendas", lazy="joined")
    cuentas_encomienda = relationship("EncomiendaCuenta", back_populates="encomienda", lazy="select")

    def __repr__(self):
        return f"<Encomienda id={self.id} estado={self.estado} pedido={self.id_pedido}>"
