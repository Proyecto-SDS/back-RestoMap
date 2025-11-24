from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base


class TipoLocal(Base):
    
    __tablename__ = "tipo_local"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(100), nullable=False)

    # Relaciones
    local = relationship("Local", back_populates="tipo_local", lazy="joined")

    def __repr__(self):
        return f"<TipoLocal id={self.id} id_local={self.id_local} nombre={self.nombre}>"
