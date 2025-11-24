from sqlalchemy import Column, Integer, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base


class Direccion(Base):
    __tablename__ = "direccion"

    id = Column(Integer, primary_key=True, index=True)
    id_comuna = Column(Integer, ForeignKey("comuna.id", ondelete="SET NULL"), nullable=True, index=True)
    numero = Column(Integer, nullable=False)
    longitud = Column(DECIMAL, nullable=False)
    latitud = Column(DECIMAL, nullable=False)

    # Relaciones
    locales = relationship("Local", back_populates="direccion", lazy="select")
    comuna = relationship("Comuna", back_populates="direcciones", lazy="joined")

    def __repr__(self):
        return (
            f"<Direccion id={self.id} numero={self.numero} "
            f"longitud={self.longitud} latitud={self.latitud}>"
        )
