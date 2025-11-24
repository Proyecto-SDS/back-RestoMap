from sqlalchemy import Column, Integer, String, SmallInteger, ForeignKey, Enum
from sqlalchemy.orm import relationship
from db.base import Base
import enum

class EstadoMesaEnum(enum.Enum):
    DISPONIBLE = 'disponible'
    RESERVADA = 'reservada'
    OCUPADA = 'ocupada'
    FUERA_DE_SERVICIO = 'fuera_de_servicio'

class Mesa(Base):
    __tablename__ = "mesa"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(30), nullable=False)
    capacidad = Column(SmallInteger, nullable=False)
    estado = Column(Enum(EstadoMesaEnum, name="estado_mesa_enum"), nullable=False, default=EstadoMesaEnum.DISPONIBLE)

    # Relaciones
    local = relationship("Local", back_populates="mesas", lazy="joined")
    reservas_mesa = relationship("Reserva_Mesa", back_populates="mesa", lazy="select", cascade="all, delete-orphan")
    qrs = relationship("QR_Dinamico", back_populates="mesa", lazy="select", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Mesa id={self.id} nombre={self.nombre} capacidad={self.capacidad} estado={self.estado}>"