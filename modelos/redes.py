from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base

class Redes(Base):

    __tablename__ = "redes"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True)
    id_foto = Column(Integer, ForeignKey("foto.id", ondelete="SET NULL"), nullable=True, index=True)
    id_tipo_red = Column(Integer, ForeignKey("tipo_red.id", ondelete="SET NULL"), nullable=True, index=True)
    url = Column(Text, nullable=False)

    # Relaciones
    local = relationship("Local", back_populates="redes", lazy="joined")
    foto = relationship("Foto", back_populates="redes", lazy="joined")
    tipo_red = relationship("TipoRed", back_populates="redes", lazy="joined")

    def __repr__(self):
        return (
            f"<Redes id={self.id} id_local={self.id_local} "
            f"id_foto={self.id_foto} id_tipo_red={self.id_tipo_red}>"
        )
