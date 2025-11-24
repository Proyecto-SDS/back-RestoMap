from sqlalchemy import Column, Integer, ForeignKey, Enum, DateTime, Time, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base
import enum

class EstadoReservaEnum(enum.Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    RECHAZADA = "rechazada"


class Reserva(Base):

    __tablename__ = "reserva"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    fecha_reserva = Column(Date, nullable=False)
    hora_reserva = Column(Time, nullable=False)
    estado = Column(Enum(EstadoReservaEnum, name="estado_reserva_enum"), nullable=False, default=EstadoReservaEnum.PENDIENTE)
    creado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expirado_el = Column(DateTime(timezone=True), nullable=True)

    usuario = relationship("Usuario", back_populates="reserva", lazy="joined")
    local = relationship("Local", back_populates="reserva", lazy="joined")
    pago = relationship("Pago", back_populates="reserva", lazy="joined")
    reserva_mesa = relationship("ReservaMesa", back_populates="reserva", lazy="select")

    def __repr__(self):
        return f"<Reserva id={self.id} fecha_reserva={self.fecha_reserva} hora_reserva={self.hora_reserva} estado={self.estado.value}>"