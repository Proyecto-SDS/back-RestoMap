from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.base import Base

class Comuna(Base):

    __tablename__= "comuna"

    id = Column(Integer, primary_key=True, index=False)
    nombre = Column(String(100), nullable=False)

    direccion = relationship("Direccion", back_populates="comuna", lazy="select")

    def __repr__(self):
        return f"<Comuna id={self.id}, nombre={self.nombre}"
