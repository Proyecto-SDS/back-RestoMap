from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class Favorito(Base):

    __tablename__ = "favorito"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False)
    agregado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario = relationship("Usuario", back_populates="favorito", lazy="joined")
    local = relationship("Local", back_populates="favorito", lazy="joined")

    def __repr__(self):
        return f"<Favorito id={self.id} usuario={self.id_usuario} local={self.id_local}>"