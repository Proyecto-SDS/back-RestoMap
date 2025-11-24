from sqlalchemy import Column, Integer, SmallInteger, String, Boolean, Date, Time, Enum, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base
import enum

class TipoHorarioEnum(enum.Enum):
    NORMAL = "normal"
    ESPECIAL = "especial"
    EVENTO = "evento"
    CERRADO = "cerrado"

class Horario(Base):
    __tablename__ = "horario"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(Enum(TipoHorarioEnum, name="tipo_horario_enum"), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    dia_semana = Column(SmallInteger, nullable=False)
    hora_apertura = Column(Time, nullable=False)
    hora_cierre = Column(Time, nullable=False)
    abierto = Column(Boolean, nullable=False, default=True)
    nota = Column(String(500), nullable=True)

    # Relaciones
    local = relationship("Local", back_populates="horarios", lazy="joined")

    def __repr__(self):
        return (
            f"<Horario id={self.id} id_local={self.id_local} tipo={self.tipo} "
            f"dia_semana={self.dia_semana} apertura={self.hora_apertura} cierre={self.hora_cierre}>"
        )
