from sqlalchemy import Column, Integer, ForeignKey 
from sqlalchemy.orm import relationship
from db.base import Base

class EncomiendaCuenta(Base):
    
    __tablename__ = "encomienda_cuenta"

    id = Column(Integer, primary_key=True, index=True)
    id_cuenta = Column(Integer, ForeignKey("cuenta.id", ondelete="CASCADE"), nullable=False)
    id_encomienda = Column(Integer, ForeignKey("encomienda.id", ondelete="CASCADE"), nullable=False)

    cuenta = relationship("Cuenta", back_populates="encomiendas_cuenta", lazy="joined")
    encomienda = relationship("Encomienda", back_populates="cuentas_encomienda", lazy="joined")

    def __repr__(self):
        return f"<EncomiendaCuenta id={self.id} id_cuenta={self.id_cuenta} id_encomienda={self.id_encomienda}>"
