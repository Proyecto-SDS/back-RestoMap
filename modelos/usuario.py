from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class Usuario(Base):

    __tablename__ = "usuario" 

    id = Column(Integer, primary_key=True, index=True)
    id_rol = Column(Integer, ForeignKey("rol.id", ondelete="SET NULL"), nullable=True)
    nombre = Column(String(100), nullable=False)  
    correo = Column(String(100), unique=True, nullable=False, index=True)
    contrasena = Column(String(200), nullable=False) 
    telefono = Column(String(32), nullable=False)
    creado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    rol = relationship("Rol", back_populates="usuarios", lazy="joined")
    opiniones = relationship("Opinion", back_populates="usuario", lazy="select")
    favoritos = relationship("Favorito", back_populates="usuario", lazy="select")
    reservas = relationship("Reserva", back_populates="usuario", lazy="select")
    pedidos = relationship("Pedido", back_populates="usuario", lazy="select")
    estados_pedidos_creados = relationship("EstadoPedido", back_populates="creado_por_usuario", lazy="select")

    def __repr__(self):
        return f"<Usuario id={self.id} nombre='{self.nombre}' correo='{self.correo}'>"