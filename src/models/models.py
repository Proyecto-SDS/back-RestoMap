"""
========================================
MODELOS SQLALCHEMY COMPLETOS + ENUMS
Sistema de Gestion de Locales, Pedidos y Reservas
Compatible con: Flask, SQLAlchemy, PostgreSQL, Pydantic v2
========================================
"""

from datetime import datetime, date, time
from enum import Enum as PyEnum
from decimal import Decimal
from typing import Optional, List, Dict

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime, Date, Time,
    Boolean, Numeric, SmallInteger, Enum, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, EmailStr, validator

# ============================================
# CONFIGURACIoN BASE
# ============================================

# Importar Base desde database.py (no crear una nueva)
from database import Base

# ============================================
# ENUMS - SECCIoN 1: PAGO
# ============================================

class MetodoPagoEnum(str, PyEnum):
    """Métodos de pago disponibles"""
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    DEBITO = "debito"
    CREDITO = "credito"
    APP_DE_PAGO = "app_de_pago"
    OTRO = "otro"

    @classmethod
    def choices(cls) -> List[tuple]:
        """Retorna lista de tuplas (valor, etiqueta) para formularios"""
        return [
            (cls.EFECTIVO, "Efectivo"),
            (cls.TRANSFERENCIA, "Transferencia"),
            (cls.DEBITO, "Débito"),
            (cls.CREDITO, "Crédito"),
            (cls.APP_DE_PAGO, "App de Pago"),
            (cls.OTRO, "Otro"),
        ]

class EstadoPagoEnum(str, PyEnum):
    """Estados de un pago"""
    PENDIENTE = "pendiente"
    COBRADO = "cobrado"
    CANCELADO = "cancelado"

    @classmethod
    def choices(cls) -> List[tuple]:
        return [
            (cls.PENDIENTE, "Pendiente"),
            (cls.COBRADO, "Cobrado"),
            (cls.CANCELADO, "Cancelado"),
        ]

# ============================================
# ENUMS - SECCIoN 2: PEDIDO
# ============================================

class EstadoPedidoEnum(str, PyEnum):
    """Estados de un pedido"""
    ABIERTO = "abierto"
    EN_PREPARACION = "en_preparacion"
    SERVIDO = "servido"
    CERRADO = "cerrado"
    CANCELADO = "cancelado"

    @classmethod
    def choices(cls) -> List[tuple]:
        return [
            (cls.ABIERTO, "Abierto"),
            (cls.EN_PREPARACION, "En Preparacion"),
            (cls.SERVIDO, "Servido"),
            (cls.CERRADO, "Cerrado"),
            (cls.CANCELADO, "Cancelado"),
        ]

    @classmethod
    def is_activo(cls, estado: "EstadoPedidoEnum") -> bool:
        """Verifica si el pedido sigue activo"""
        return estado not in [cls.CERRADO, cls.CANCELADO]

# ============================================
# ENUMS - SECCIoN 3: MESA Y RESERVA
# ============================================

class EstadoMesaEnum(str, PyEnum):
    """Estados de una mesa"""
    DISPONIBLE = "disponible"
    RESERVADA = "reservada"
    OCUPADA = "ocupada"
    FUERA_DE_SERVICIO = "fuera_de_servicio"

    @classmethod
    def choices(cls) -> List[tuple]:
        return [
            (cls.DISPONIBLE, "Disponible"),
            (cls.RESERVADA, "Reservada"),
            (cls.OCUPADA, "Ocupada"),
            (cls.FUERA_DE_SERVICIO, "Fuera de Servicio"),
        ]

    @classmethod
    def puede_reservar(cls, estado: "EstadoMesaEnum") -> bool:
        """Verifica si la mesa puede ser reservada"""
        return estado == cls.DISPONIBLE

class EstadoReservaEnum(str, PyEnum):
    """Estados de una reserva"""
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    RECHAZADA = "rechazada"

    @classmethod
    def choices(cls) -> List[tuple]:
        return [
            (cls.PENDIENTE, "Pendiente"),
            (cls.CONFIRMADA, "Confirmada"),
            (cls.RECHAZADA, "Rechazada"),
        ]

class EstadoReservaMesaEnum(str, PyEnum):
    """Prioridad de una mesa en una reserva"""
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"

    @classmethod
    def choices(cls) -> List[tuple]:
        return [
            (cls.ALTA, "Alta"),
            (cls.MEDIA, "Media"),
            (cls.BAJA, "Baja"),
        ]

# ============================================
# ENUMS - SECCIoN 4: PRODUCTO Y ENCOMIENDA
# ============================================

class EstadoProductoEnum(str, PyEnum):
    """Estados de un producto"""
    DISPONIBLE = "disponible"
    AGOTADO = "agotado"
    INACTIVO = "inactivo"

    @classmethod
    def choices(cls) -> List[tuple]:
        return [
            (cls.DISPONIBLE, "Disponible"),
            (cls.AGOTADO, "Agotado"),
            (cls.INACTIVO, "Inactivo"),
        ]

    @classmethod
    def puede_vender(cls, estado: "EstadoProductoEnum") -> bool:
        """Verifica si el producto puede venderse"""
        return estado == cls.DISPONIBLE

class EstadoEncomiendaEnum(str, PyEnum):
    """Estados de una encomienda"""
    PENDIENTE = "pendiente"
    EN_PREPARACION = "en_preparacion"
    LISTA = "lista"
    ENTREGADA = "entregada"
    CANCELADA = "cancelada"

    @classmethod
    def choices(cls) -> List[tuple]:
        return [
            (cls.PENDIENTE, "Pendiente"),
            (cls.EN_PREPARACION, "En Preparacion"),
            (cls.LISTA, "Lista"),
            (cls.ENTREGADA, "Entregada"),
            (cls.CANCELADA, "Cancelada"),
        ]

# ============================================
# ENUMS - SECCIoN 5: ADICIONALES
# ============================================

class RolEnum(str, PyEnum):
    """Roles de usuario en el sistema"""
    ADMIN = "admin"
    GERENTE = "gerente"
    CHEF = "chef"
    MESERO = "mesero"
    CLIENTE = "cliente"

    @classmethod
    def choices(cls) -> List[tuple]:
        return [
            (cls.ADMIN, "Administrador"),
            (cls.GERENTE, "Gerente"),
            (cls.CHEF, "Chef"),
            (cls.MESERO, "Mesero"),
            (cls.CLIENTE, "Cliente"),
        ]

class TipoHorarioEnum(str, PyEnum):
    """Tipos de horarios especiales"""
    NORMAL = "normal"
    ESPECIAL = "especial"
    EVENTO = "evento"
    CERRADO = "cerrado"

    @classmethod
    def choices(cls) -> List[tuple]:
        return [
            (cls.NORMAL, "Normal"),
            (cls.ESPECIAL, "Especial"),
            (cls.EVENTO, "Evento"),
            (cls.CERRADO, "Cerrado"),
        ]

# ============================================
# FUNCIONES AUXILIARES DE ENUMS
# ============================================

def obtener_etiqueta(enum_class, valor: str) -> str:
    """Obtiene la etiqueta legible de un enum"""
    for enum_value, etiqueta in enum_class.choices():
        if enum_value.value == valor:
            return etiqueta
    return valor

def obtener_colores_estado(enum_value) -> Dict[str, str]:
    """Retorna color y icono para mostrar estados en frontend"""
    color_map = {
        # Pedidos
        EstadoPedidoEnum.ABIERTO: {"color": "blue", "icono": "🟦", "label": "Abierto"},
        EstadoPedidoEnum.EN_PREPARACION: {"color": "orange", "icono": "🟧", "label": "Preparando"},
        EstadoPedidoEnum.SERVIDO: {"color": "purple", "icono": "🟪", "label": "Servido"},
        EstadoPedidoEnum.CERRADO: {"color": "green", "icono": "🟩", "label": "Cerrado"},
        EstadoPedidoEnum.CANCELADO: {"color": "red", "icono": "🟥", "label": "Cancelado"},
        
        # Mesas
        EstadoMesaEnum.DISPONIBLE: {"color": "green", "icono": "", "label": "Disponible"},
        EstadoMesaEnum.RESERVADA: {"color": "yellow", "icono": "", "label": "Reservada"},
        EstadoMesaEnum.OCUPADA: {"color": "orange", "icono": "", "label": "Ocupada"},
        EstadoMesaEnum.FUERA_DE_SERVICIO: {"color": "red", "icono": "", "label": "Fuera de Servicio"},
    }
    
    return color_map.get(enum_value, {"color": "gray", "icono": "", "label": str(enum_value)})

def validar_transicion_estado(estado_actual, estado_nuevo, enum_class) -> bool:
    """Valida si la transicion de estados es permitida"""
    transiciones_validas = {
        EstadoPedidoEnum: {
            EstadoPedidoEnum.ABIERTO: [EstadoPedidoEnum.EN_PREPARACION, EstadoPedidoEnum.CANCELADO],
            EstadoPedidoEnum.EN_PREPARACION: [EstadoPedidoEnum.SERVIDO, EstadoPedidoEnum.CANCELADO],
            EstadoPedidoEnum.SERVIDO: [EstadoPedidoEnum.CERRADO],
            EstadoPedidoEnum.CERRADO: [],
            EstadoPedidoEnum.CANCELADO: [],
        },
        EstadoMesaEnum: {
            EstadoMesaEnum.DISPONIBLE: [EstadoMesaEnum.RESERVADA, EstadoMesaEnum.OCUPADA],
            EstadoMesaEnum.RESERVADA: [EstadoMesaEnum.DISPONIBLE, EstadoMesaEnum.OCUPADA],
            EstadoMesaEnum.OCUPADA: [EstadoMesaEnum.DISPONIBLE],
            EstadoMesaEnum.FUERA_DE_SERVICIO: [EstadoMesaEnum.DISPONIBLE],
        },
    }
    
    transiciones = transiciones_validas.get(enum_class, {})
    permitidas = transiciones.get(estado_actual, [])
    
    return estado_nuevo in permitidas

# ============================================
# TABLAS DE REFERENCIA
# ============================================

class Rol(Base):
    __tablename__ = "rol"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    
    usuarios = relationship("Usuario", back_populates="rol", lazy="select")

class Comuna(Base):
    __tablename__ = "comuna"
    
    id = Column(Integer, primary_key=True, index=False)
    nombre = Column(String(100), nullable=False, unique=True)
    
    direcciones = relationship("Direccion", back_populates="comuna", lazy="select")

class TipoLocal(Base):
    __tablename__ = "tipo_local"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    
    locales = relationship("Local", back_populates="tipo_local", lazy="select")

class TipoRed(Base):
    __tablename__ = "tipo_red"
    
    id = Column(Integer, primary_key=True, index=False)
    nombre = Column(String(100), nullable=False, unique=True)
    
    redes = relationship("Redes", back_populates="tipo_red", lazy="select")

class TipoFoto(Base):
    __tablename__ = "tipo_foto"
    
    id = Column(Integer, primary_key=True, index=False)
    nombre = Column(String(100), nullable=False, unique=True)
    
    fotos = relationship("Foto", back_populates="tipo_foto", lazy="select")

class Categoria(Base):
    __tablename__ = "categoria"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    
    productos = relationship("Producto", back_populates="categoria", lazy="selectin")
    fotos = relationship("Foto", back_populates="categoria", lazy="selectin")

# ============================================
# UBICACIoN
# ============================================

class Direccion(Base):
    __tablename__ = "direccion"
    
    id = Column(Integer, primary_key=True, index=True)
    id_comuna = Column(Integer, ForeignKey("comuna.id", ondelete="SET NULL"), nullable=True, index=True)
    calle = Column(String(200), nullable=False)
    numero = Column(Integer, nullable=False)
    longitud = Column(Numeric, nullable=False)
    latitud = Column(Numeric, nullable=False)
    
    locales = relationship("Local", back_populates="direccion", lazy="select")
    comuna = relationship("Comuna", back_populates="direcciones", lazy="joined")

# ============================================
# LOCALES Y CONFIGURACIoN
# ============================================

class Local(Base):
    __tablename__ = "local"
    
    id = Column(Integer, primary_key=True, index=True)
    id_direccion = Column(Integer, ForeignKey("direccion.id", ondelete="CASCADE"), nullable=False, index=True)
    id_tipo_local = Column(Integer, ForeignKey("tipo_local.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    telefono = Column(Integer, nullable=False)
    correo = Column(String(50), nullable=False, unique=True, index=True)
    
    horarios = relationship("Horario", back_populates="local", lazy="select", cascade="all, delete-orphan")
    direccion = relationship("Direccion", back_populates="locales", lazy="joined")
    productos = relationship("Producto", back_populates="local", lazy="select", cascade="all, delete-orphan")
    tipo_local = relationship("TipoLocal", back_populates="locales", lazy="joined")
    redes = relationship("Redes", back_populates="local", lazy="select", cascade="all, delete-orphan")
    fotos = relationship("Foto", back_populates="local", lazy="select", cascade="all, delete-orphan")
    mesas = relationship("Mesa", back_populates="local", lazy="select", cascade="all, delete-orphan")
    opiniones = relationship("Opinion", back_populates="local", lazy="select", cascade="all, delete-orphan")
    favoritos = relationship("Favorito", back_populates="local", lazy="select", cascade="all, delete-orphan")
    reservas = relationship("Reserva", back_populates="local", lazy="select", cascade="all, delete-orphan")
    pedidos = relationship("Pedido", back_populates="local", lazy="select", cascade="all, delete-orphan")

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
    
    local = relationship("Local", back_populates="horarios", lazy="joined")

class Mesa(Base):
    __tablename__ = "mesa"
    
    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(30), nullable=False)
    descripcion = Column(String(100), nullable=True)
    capacidad = Column(SmallInteger, nullable=False)
    estado = Column(Enum(EstadoMesaEnum, name="estado_mesa_enum"), nullable=False, default=EstadoMesaEnum.DISPONIBLE)
    
    local = relationship("Local", back_populates="mesas", lazy="joined")
    reservas_mesa = relationship("ReservaMesa", back_populates="mesa", lazy="select", cascade="all, delete-orphan")
    qr_dinamicos = relationship("QRDinamico", back_populates="mesa", lazy="select", cascade="all, delete-orphan")

# ============================================
# USUARIOS Y AUTENTICACIoN
# ============================================

class Usuario(Base):
    __tablename__ = "usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    id_rol = Column(Integer, ForeignKey("rol.id", ondelete="SET NULL"), nullable=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(100), unique=True, nullable=False, index=True)
    contrasena = Column(String(200), nullable=False)
    telefono = Column(String(32), nullable=False)
    creado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    rol = relationship("Rol", back_populates="usuarios", lazy="joined")
    opiniones = relationship("Opinion", back_populates="usuario", lazy="select", cascade="all, delete-orphan")
    favoritos = relationship("Favorito", back_populates="usuario", lazy="select", cascade="all, delete-orphan")
    reservas = relationship("Reserva", back_populates="usuario", lazy="select", cascade="all, delete-orphan")
    pedidos = relationship("Pedido", back_populates="usuario", lazy="select", cascade="all, delete-orphan")
    estados_pedido = relationship("EstadoPedido", back_populates="creado_por_usuario", lazy="select")

# ============================================
# CONTENIDO MULTIMEDIA
# ============================================

class Foto(Base):
    __tablename__ = "foto"
    
    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=True, index=True)
    id_producto = Column(Integer, ForeignKey("producto.id", ondelete="SET NULL"), nullable=True, index=True)
    id_categoria = Column(Integer, ForeignKey("categoria.id", ondelete="SET NULL"), nullable=True, index=True)
    id_tipo_foto = Column(Integer, ForeignKey("tipo_foto.id", ondelete="SET NULL"), nullable=True, index=True)
    ruta = Column(Text, nullable=False)
    
    local = relationship("Local", back_populates="fotos", lazy="joined")
    producto = relationship("Producto", back_populates="fotos", lazy="joined")
    categoria = relationship("Categoria", back_populates="fotos", lazy="joined")
    tipo_foto = relationship("TipoFoto", back_populates="fotos", lazy="joined")
    redes = relationship("Redes", back_populates="foto", lazy="select")

class Redes(Base):
    __tablename__ = "redes"
    
    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True)
    id_foto = Column(Integer, ForeignKey("foto.id", ondelete="SET NULL"), nullable=True, index=True)
    id_tipo_red = Column(Integer, ForeignKey("tipo_red.id", ondelete="SET NULL"), nullable=True, index=True)
    nombre_usuario = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    
    local = relationship("Local", back_populates="redes", lazy="joined")
    foto = relationship("Foto", back_populates="redes", lazy="joined")
    tipo_red = relationship("TipoRed", back_populates="redes", lazy="joined")

# ============================================
# CATaLOGO DE PRODUCTOS
# ============================================

class Producto(Base):
    __tablename__ = "producto"
    
    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True)
    id_categoria = Column(Integer, ForeignKey("categoria.id", ondelete="SET NULL"), nullable=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(500), nullable=True)
    estado = Column(Enum(EstadoProductoEnum, name="estado_producto_enum"), nullable=False, default=EstadoProductoEnum.DISPONIBLE)
    precio = Column(Integer, nullable=False)
    
    local = relationship("Local", back_populates="productos", lazy="joined")
    categoria = relationship("Categoria", back_populates="productos", lazy="joined")
    fotos = relationship("Foto", back_populates="producto", lazy="select", cascade="all, delete-orphan")
    cuentas = relationship("Cuenta", back_populates="producto", lazy="select")

# ============================================
# OPINIONES Y VALORACIONES
# ============================================

class Opinion(Base):
    __tablename__ = "opinion"
    
    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True)
    puntuacion = Column(Numeric(2, 1), nullable=False)
    comentario = Column(String(500), nullable=False)
    creado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    eliminado_el = Column(DateTime(timezone=True), nullable=True)
    
    usuario = relationship("Usuario", back_populates="opiniones", lazy="joined")
    local = relationship("Local", back_populates="opiniones", lazy="joined")

# ============================================
# FAVORITOS
# ============================================

class Favorito(Base):
    __tablename__ = "favorito"
    
    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True)
    agregado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    __table_args__ = (
        UniqueConstraint('id_usuario', 'id_local', name='uq_usuario_local_favorito'),
    )
    
    usuario = relationship("Usuario", back_populates="favoritos", lazy="joined")
    local = relationship("Local", back_populates="favoritos", lazy="joined")

# ============================================
# RESERVAS
# ============================================

class Reserva(Base):
    __tablename__ = "reserva"
    
    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False, index=True)
    fecha_reserva = Column(Date, nullable=False)
    hora_reserva = Column(Time, nullable=False)
    estado = Column(Enum(EstadoReservaEnum, name="estado_reserva_enum"), nullable=False, default=EstadoReservaEnum.PENDIENTE)
    creado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    expirado_el = Column(DateTime(timezone=True), nullable=True)
    
    usuario = relationship("Usuario", back_populates="reservas", lazy="joined")
    local = relationship("Local", back_populates="reservas", lazy="joined")
    reservas_mesa = relationship("ReservaMesa", back_populates="reserva", lazy="select", cascade="all, delete-orphan")
    qr_dinamicos = relationship("QRDinamico", back_populates="reserva", lazy="select", cascade="all, delete-orphan")

class ReservaMesa(Base):
    __tablename__ = "reserva_mesa"
    
    id = Column(Integer, primary_key=True, index=False)
    id_reserva = Column(Integer, ForeignKey("reserva.id", ondelete="CASCADE"), nullable=False, index=True)
    id_mesa = Column(Integer, ForeignKey("mesa.id", ondelete="CASCADE"), nullable=False, index=True)
    prioridad = Column(Enum(EstadoReservaMesaEnum, name="estado_reserva_mesa_enum"), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('id_reserva', 'id_mesa', name='uq_reserva_mesa'),
    )
    
    reserva = relationship("Reserva", back_populates="reservas_mesa", lazy="joined")
    mesa = relationship("Mesa", back_populates="reservas_mesa", lazy="joined")

# ============================================
# PEDIDOS
# ============================================

class Pedido(Base):
    __tablename__ = "pedido"
    
    id = Column(Integer, primary_key=True, index=True)
    local_id = Column(Integer, ForeignKey("local.id", ondelete="SET NULL"), nullable=True, index=True)
    mesa_id = Column(Integer, ForeignKey("mesa.id", ondelete="SET NULL"), nullable=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True, index=True)
    estado = Column(Enum(EstadoPedidoEnum, name="estado_pedido_enum"), nullable=False, default=EstadoPedidoEnum.ABIERTO)
    total = Column(Integer, nullable=False, default=0)
    creado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    actualizado_el = Column(DateTime(timezone=True), onupdate=func.now())
    
    local = relationship("Local", back_populates="pedidos", lazy="joined")
    mesa = relationship("Mesa", lazy="joined")
    usuario = relationship("Usuario", back_populates="pedidos", lazy="joined")
    cuentas = relationship("Cuenta", back_populates="pedido", lazy="select", cascade="all, delete-orphan")
    encomiendas = relationship("Encomienda", back_populates="pedido", lazy="select", cascade="all, delete-orphan")
    estado_pedido = relationship("EstadoPedido", back_populates="pedido", lazy="select", cascade="all, delete-orphan")
    pagos = relationship("Pago", back_populates="pedido", lazy="select")
    qr_dinamicos = relationship("QRDinamico", back_populates="pedido", lazy="select")

class Cuenta(Base):
    __tablename__ = "cuenta"
    
    id = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False, index=True)
    id_producto = Column(Integer, ForeignKey("producto.id", ondelete="CASCADE"), nullable=False, index=True)
    cantidad = Column(Integer, nullable=False)
    observaciones = Column(String(500), nullable=False)
    
    pedido = relationship("Pedido", back_populates="cuentas", lazy="joined")
    producto = relationship("Producto", back_populates="cuentas", lazy="joined")
    encomiendas_cuenta = relationship("EncomiendaCuenta", back_populates="cuenta", lazy="select", cascade="all, delete-orphan")

class EstadoPedido(Base):
    __tablename__ = "estado_pedido"
    
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False, index=True)
    estado = Column(Enum(EstadoPedidoEnum, name="estado_pedido_enum"), nullable=False)
    creado_por = Column(Integer, ForeignKey("usuario.id"), nullable=False, index=True)
    creado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    pedido = relationship("Pedido", back_populates="estado_pedido", lazy="joined")
    creado_por_usuario = relationship("Usuario", back_populates="estados_pedido", lazy="joined", foreign_keys=[creado_por])

# ============================================
# QR DINaMICO
# ============================================

class QRDinamico(Base):
    __tablename__ = "qr_dinamico"
    
    id = Column(Integer, primary_key=True, index=False)
    id_mesa = Column(Integer, ForeignKey("mesa.id", ondelete="CASCADE"), nullable=False, index=True)
    id_pedido = Column(Integer, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=True, index=True)
    id_reserva = Column(Integer, ForeignKey("reserva.id", ondelete="CASCADE"), nullable=True, index=True)
    codigo = Column(String(255), nullable=False, unique=True)
    expiracion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    
    mesa = relationship("Mesa", back_populates="qr_dinamicos", lazy="joined")
    pedido = relationship("Pedido", back_populates="qr_dinamicos", lazy="joined")
    reserva = relationship("Reserva", back_populates="qr_dinamicos", lazy="joined")

# ============================================
# ENCOMIENDAS
# ============================================

class Encomienda(Base):
    __tablename__ = "encomienda"
    
    id = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False, index=True)
    estado = Column(Enum(EstadoEncomiendaEnum, name="estado_encomienda_enum"), nullable=False)
    creado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    pedido = relationship("Pedido", back_populates="encomiendas", lazy="joined")
    cuentas_encomienda = relationship("EncomiendaCuenta", back_populates="encomienda", lazy="select", cascade="all, delete-orphan")

class EncomiendaCuenta(Base):
    __tablename__ = "encomienda_cuenta"
    
    id = Column(Integer, primary_key=True, index=True)
    id_cuenta = Column(Integer, ForeignKey("cuenta.id", ondelete="CASCADE"), nullable=False, index=True)
    id_encomienda = Column(Integer, ForeignKey("encomienda.id", ondelete="CASCADE"), nullable=False, index=True)
    
    cuenta = relationship("Cuenta", back_populates="encomiendas_cuenta", lazy="joined")
    encomienda = relationship("Encomienda", back_populates="cuentas_encomienda", lazy="joined")

# ============================================
# PAGOS
# ============================================

class Pago(Base):
    __tablename__ = "pago"
    
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedido.id", ondelete="SET NULL"), nullable=True, index=True)
    metodo = Column(Enum(MetodoPagoEnum, name="metodo_pago_enum"), nullable=False)
    estado = Column(Enum(EstadoPagoEnum, name="estado_pago_enum"), nullable=False, default=EstadoPagoEnum.PENDIENTE)
    monto = Column(Integer, nullable=False)
    creado_el = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    actualizado_el = Column(DateTime(timezone=True), onupdate=func.now())
    
    pedido = relationship("Pedido", back_populates="pagos", lazy="joined")

# ============================================
# SCHEMAS PYDANTIC V2
# ============================================

class RolSchema(BaseModel):
    id: Optional[int] = None
    nombre: str

    class Config:
        from_attributes = True

class UsuarioSchema(BaseModel):
    id: Optional[int] = None
    nombre: str
    correo: EmailStr
    telefono: str
    id_rol: Optional[int] = None

    class Config:
        from_attributes = True

class LocalSchema(BaseModel):
    id: Optional[int] = None
    nombre: str
    telefono: int
    correo: str
    id_direccion: int
    id_tipo_local: int

    class Config:
        from_attributes = True

class ProductoSchema(BaseModel):
    id: Optional[int] = None
    nombre: str
    descripcion: Optional[str] = None
    precio: int
    estado: EstadoProductoEnum
    id_local: int
    id_categoria: Optional[int] = None

    class Config:
        from_attributes = True

class PedidoSchema(BaseModel):
    id: Optional[int] = None
    estado: EstadoPedidoEnum
    total: int
    local_id: Optional[int] = None
    mesa_id: Optional[int] = None
    usuario_id: Optional[int] = None

    class Config:
        from_attributes = True

class PagoSchema(BaseModel):
    id: Optional[int] = None
    monto: int
    metodo: MetodoPagoEnum
    estado: EstadoPagoEnum
    pedido_id: Optional[int] = None

    class Config:
        from_attributes = True

class MesaSchema(BaseModel):
    id: Optional[int] = None
    id_local: int
    nombre: str
    descripcion: Optional[str] = None
    capacidad: int
    estado: EstadoMesaEnum

    class Config:
        from_attributes = True

class QRDinamicoSchema(BaseModel):
    id: Optional[int] = None
    id_mesa: int
    id_pedido: Optional[int] = None
    id_reserva: Optional[int] = None
    codigo: str
    expiracion: datetime
    activo: bool

    class Config:
        from_attributes = True

class ReservaSchema(BaseModel):
    id: Optional[int] = None
    id_local: int
    id_usuario: int
    fecha_reserva: date
    hora_reserva: time
    estado: EstadoReservaEnum
    creado_el: Optional[datetime] = None
    expirado_el: Optional[datetime] = None

    class Config:
        from_attributes = True

class OpinionSchema(BaseModel):
    id: Optional[int] = None
    id_usuario: int
    id_local: int
    puntuacion: float
    comentario: str
    creado_el: Optional[datetime] = None
    eliminado_el: Optional[datetime] = None

    class Config:
        from_attributes = True

class CuentaSchema(BaseModel):
    id: Optional[int] = None
    id_pedido: int
    id_producto: int
    cantidad: int
    observaciones: str

    class Config:
        from_attributes = True

class EncomiendaSchema(BaseModel):
    id: Optional[int] = None
    id_pedido: int
    estado: EstadoEncomiendaEnum
    creado_el: Optional[datetime] = None

    class Config:
        from_attributes = True
