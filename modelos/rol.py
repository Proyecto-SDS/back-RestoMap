from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.base import Base

class Rol(Base):
    
    __tablename__ = 'rol'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    
    usuarios = relationship("Usuario", back_populates="rol", lazy="select")

    def __repr__(self):
        return f"<Rol id={self.id} nombre='{self.nombre}'>"