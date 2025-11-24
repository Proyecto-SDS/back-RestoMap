from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class Opinion(Base):

    __tablename__ = "opinion"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False)
    puntuacion = Column(Numeric(2, 1), nullable=False)
    comentario = Column(String(500), nullable=False)
    creado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    eliminado_el = Column(DateTime(timezone=True), nullable=True)  # soft-delete timestamp

    usuario = relationship("Usuario", back_populates="opiniones", lazy="joined")
    local = relationship("Local", back_populates="opiniones", lazy="joined")

    def __repr__(self):
        return f"<Opinion id={self.id} usuario={self.id_usuario} local={self.id_local} puntuacion={self.puntuacion}>"