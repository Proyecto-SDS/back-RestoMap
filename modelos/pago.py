from sqlalchemy import Column, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from db.base import Base
import enum

class MetodoPagoEnum(enum.Enum):
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    DEBITO = "debito"
    CREDITO = "credito"
    APP_DE_PAGO = "app_de_pago"
    OTRO = "otro"

class EstadoPagoEnum(enum.Enum):
    PENDIENTE = "pendiente"
    COBRADO = "cobrado"
    CANCELADO = "cancelado"

class Pago(Base):

    __tablename__ = "pago"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedido.id", ondelete="SET NULL"), nullable=True)
    reserva_id = Column(Integer, ForeignKey("reserva.id", ondelete="SET NULL"), nullable=True)
    metodo = Column(Enum(MetodoPagoEnum, name="metodo_pago_enum"), nullable=False)
    estado = Column(Enum(EstadoPagoEnum, name="estado_pago_enum"), nullable=False, default=EstadoPagoEnum.PENDIENTE)
    monto = Column(Integer, nullable=False)

    pedido = relationship("Pedido", back_populates="pagos")
    reserva = relationship("Reserva", back_populates="pagos")

    def __repr__(self):
        return f"<Pago id={self.id} metodo={self.metodo.value} estado={self.estado.value}>"