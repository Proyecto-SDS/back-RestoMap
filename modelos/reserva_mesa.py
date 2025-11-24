from sqlalchemy import Column, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from db.base import Base
import enum 

class EstadoReservaMesa(enum.Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class ReservaMesa(Base):

    __tablename__= "reserva_mesa"

    id = Column(Integer, primary_key=True, index=False)
    id_reserva = Column(Integer, ForeignKey("reserva.id", ondelete="CASCADE"), nullable=False)
    id_mesa = Column(Integer, ForeignKey("mesa.id", ondelete="CASCADE"), nullable=False)
    prioridad = Column(Enum(EstadoReservaMesa, name= "estado_reserva_mesa_enum"), nullable=False)

    reserva = relationship("Reserva", back_populates="reserva_mesa",lazy="joined")
    mesa = relationship("Mesa", back_populates="reserva_mesa", lazy="joined")

    def __repr__(self):
        return f"<reserva_Mesa id={self.id} reserva={self.id_reserva} mesa={self.id_mesa} prioridad={self.prioridad}"