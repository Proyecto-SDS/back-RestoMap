from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base
import enum

class EstadoPedidoEnum(enum.Enum):
    ABIERTO = "abierto"
    EN_PREPARACION = "en_preparacion"
    SERVIDO = "servido"
    CERRADO = "cerrado"
    CANCELADO = "cancelado"

class Pedido(Base):

    __tablename__ = "pedido"

    id = Column(Integer, primary_key=True, index=True)
    local_id = Column(Integer, ForeignKey("local.id", ondelete="SET NULL"), nullable=True)
    mesa_id = Column(Integer, ForeignKey("mesa.id", ondelete="SET NULL"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True)
    estado = Column(Enum(EstadoPedidoEnum, name="estado_pedido_enum"), nullable=False, default=EstadoPedidoEnum.ABIERTO)
    total = Column(Integer, nullable=False, default=0)
    creado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actualizado_el = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    local = relationship("Local", back_populates="pedido", lazy="joined")
    mesa = relationship("Mesa", back_populates="pedido", lazy="joined")
    usuario = relationship("Usuario", back_populates="pedido", lazy="joined")
    cuentas = relationship("Cuenta", back_populates="pedido", cascade="all, delete-orphan", lazy="select")
    pagos = relationship("Pago", back_populates="pedido", lazy="select")
    encomiendas = relationship("Encomienda", back_populates="pedido", lazy="select")
    estado_pedido = relationship("EstadoPedido", back_populates="pedido", lazy="select")

    def __repr__(self):
        return f"<Pedido id={self.id} local={self.local_id} mesa={self.mesa_id} usuario={self.usuario_id} estado={self.estado} total={self.total}>"