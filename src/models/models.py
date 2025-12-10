"""
========================================
MODELOS SQLALCHEMY COMPLETOS + ENUMS
Sistema de Gestion de Locales, Pedidos y Reservas
Compatible con: Flask, SQLAlchemy, PostgreSQL, Pydantic v2
========================================
CAMBIOS FINALES:
- Eliminado prioridad de ReservaMesa (se calcula dinámicamente)
- Prioridad calculada por fecha-hora de reserva (backend)
========================================
"""

from datetime import date, datetime, time
from enum import Enum as PyEnum

from pydantic import BaseModel, EmailStr
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

# ============================================
# CONFIGURACIÓN BASE
# ============================================
from database import Base

# ============================================
# ENUMS - SECCIÓN 1: PAGO
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
    def choices(cls) -> list[tuple]:
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
    def choices(cls) -> list[tuple]:
        return [
            (cls.PENDIENTE, "Pendiente"),
            (cls.COBRADO, "Cobrado"),
            (cls.CANCELADO, "Cancelado"),
        ]


# ============================================
# ENUMS - SECCIÓN 2: PEDIDO
# ============================================


class EstadoPedidoEnum(str, PyEnum):
    """Estados de un pedido - ACTUALIZADO según auditoría"""

    INICIADO = "iniciado"  # Pedido creado desde QR
    RECEPCION = "recepcion"  # Pedido recibido
    EN_PROCESO = "en_proceso"  # Se está preparando
    TERMINADO = "terminado"  # Listo para servir
    SERVIDO = "servido"  # Mesero confirma entrega
    COMPLETADO = "completado"  # Pagado y cerrado
    CANCELADO = "cancelado"

    @classmethod
    def choices(cls) -> list[tuple]:
        return [
            (cls.INICIADO, "Iniciado"),
            (cls.RECEPCION, "Recepción"),
            (cls.EN_PROCESO, "En Proceso"),
            (cls.TERMINADO, "Terminado"),
            (cls.SERVIDO, "Servido"),
            (cls.COMPLETADO, "Completado"),
            (cls.CANCELADO, "Cancelado"),
        ]

    @classmethod
    def is_activo(cls, estado: "EstadoPedidoEnum") -> bool:
        """Verifica si el pedido sigue activo"""
        return estado not in [cls.COMPLETADO, cls.CANCELADO]

    @classmethod
    def flujo_valido(
        cls, estado_actual: "EstadoPedidoEnum", estado_nuevo: "EstadoPedidoEnum"
    ) -> bool:
        """Valida transiciones permitidas en el flujo de pedidos"""
        transiciones = {
            cls.INICIADO: [cls.RECEPCION, cls.CANCELADO],
            cls.RECEPCION: [cls.EN_PROCESO, cls.CANCELADO],
            cls.EN_PROCESO: [cls.TERMINADO, cls.CANCELADO],
            cls.TERMINADO: [cls.SERVIDO, cls.CANCELADO],
            cls.SERVIDO: [cls.COMPLETADO],
            cls.COMPLETADO: [],
            cls.CANCELADO: [],
        }
        return estado_nuevo in transiciones.get(estado_actual, [])


# Tiempos de extensión por estado (en minutos)
# Estos tiempos se ACUMULAN al cambiar de estado
TIEMPO_EXTENSION_POR_ESTADO = {
    EstadoPedidoEnum.INICIADO: 15,  # Al escanear QR
    EstadoPedidoEnum.RECEPCION: 45,  # Al agregar productos
    EstadoPedidoEnum.EN_PROCESO: 15,  # Al comenzar preparación
    # TERMINADO y SERVIDO no extienden, solo generan alertas
}


# ============================================
# ENUMS - SECCIÓN 3: MESA Y RESERVA
# ============================================


class EstadoMesaEnum(str, PyEnum):
    """Estados de una mesa"""

    DISPONIBLE = "disponible"
    RESERVADA = "reservada"
    OCUPADA = "ocupada"
    FUERA_DE_SERVICIO = "fuera_de_servicio"

    @classmethod
    def choices(cls) -> list[tuple]:
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
    EXPIRADA = "expirada"  # Para reservas que expiraron

    @classmethod
    def choices(cls) -> list[tuple]:
        return [
            (cls.PENDIENTE, "Pendiente"),
            (cls.CONFIRMADA, "Confirmada"),
            (cls.RECHAZADA, "Rechazada"),
            (cls.EXPIRADA, "Expirada"),
        ]


# ============================================
# ENUMS - SECCIÓN 4: PRODUCTO Y ENCOMIENDA
# ============================================


class EstadoProductoEnum(str, PyEnum):
    """Estados de un producto"""

    DISPONIBLE = "disponible"
    AGOTADO = "agotado"
    INACTIVO = "inactivo"

    @classmethod
    def choices(cls) -> list[tuple]:
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
    def choices(cls) -> list[tuple]:
        return [
            (cls.PENDIENTE, "Pendiente"),
            (cls.EN_PREPARACION, "En Preparación"),
            (cls.LISTA, "Lista"),
            (cls.ENTREGADA, "Entregada"),
            (cls.CANCELADA, "Cancelada"),
        ]


# ============================================
# ENUMS - SECCIÓN 5: ADICIONALES
# ============================================


class RolEnum(str, PyEnum):
    """Roles de usuario en el sistema"""

    ADMIN = "admin"
    GERENTE = "gerente"
    CHEF = "chef"
    MESERO = "mesero"
    CLIENTE = "cliente"

    @classmethod
    def choices(cls) -> list[tuple]:
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
    def choices(cls) -> list[tuple]:
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


def obtener_prioridad_reserva(
    fecha_reserva: date | Column[date] | None, hora_reserva: time | Column[time] | None
) -> str | None:
    """
    Calcula DINAMICAMENTE la prioridad de una reserva segun cercania a la hora actual.

    - ALTA: Dentro de 2 horas
    - MEDIA: Dentro de 24 horas
    - BAJA: Mas de 24 horas

    Esta es la forma correcta de hacerlo (no como campo en BD)
    """
    if fecha_reserva is None or hora_reserva is None:
        return None

    from datetime import datetime

    ahora = datetime.now()
    reserva_datetime = datetime.combine(fecha_reserva, hora_reserva)  # type: ignore
    diferencia_horas = (reserva_datetime - ahora).total_seconds() / 3600

    if diferencia_horas <= 2:
        return "alta"
    elif diferencia_horas <= 24:
        return "media"
    else:
        return "baja"


def validar_transicion_estado(estado_actual, estado_nuevo, enum_class) -> bool:
    """
    Valida si la transición de estados es permitida.

    Para pedidos, delega al método flujo_valido() de EstadoPedidoEnum.
    Para otros enums, usa lógica de transiciones definida aquí.
    """
    # Para pedidos, usar el método de la clase
    if enum_class == EstadoPedidoEnum:
        return EstadoPedidoEnum.flujo_valido(estado_actual, estado_nuevo)

    # Para otros enums (mesas, etc.)
    transiciones_validas = {
        EstadoMesaEnum: {
            EstadoMesaEnum.DISPONIBLE: [
                EstadoMesaEnum.RESERVADA,
                EstadoMesaEnum.OCUPADA,
            ],
            EstadoMesaEnum.RESERVADA: [
                EstadoMesaEnum.DISPONIBLE,
                EstadoMesaEnum.OCUPADA,
            ],
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


class TipoCategoria(Base):
    """Tipo de categoria: Comida o Bebida - para filtrar en cocina/barra"""

    __tablename__ = "tipo_categoria"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False, unique=True)

    categorias = relationship(
        "Categoria", back_populates="tipo_categoria", lazy="select"
    )


class Categoria(Base):
    __tablename__ = "categoria"

    id = Column(Integer, primary_key=True, index=True)
    id_tipo_categoria = Column(
        Integer,
        ForeignKey("tipo_categoria.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    nombre = Column(String(100), nullable=False, unique=True)

    tipo_categoria = relationship(
        "TipoCategoria", back_populates="categorias", lazy="joined"
    )
    productos = relationship("Producto", back_populates="categoria", lazy="selectin")
    fotos = relationship("Foto", back_populates="categoria", lazy="selectin")


# ============================================
# UBICACIÓN
# ============================================


class Direccion(Base):
    __tablename__ = "direccion"

    id = Column(Integer, primary_key=True, index=True)
    id_comuna = Column(
        Integer, ForeignKey("comuna.id", ondelete="SET NULL"), nullable=True, index=True
    )
    calle = Column(String(200), nullable=False)
    numero = Column(Integer, nullable=False)
    longitud = Column(Numeric, nullable=False)
    latitud = Column(Numeric, nullable=False)

    locales = relationship("Local", back_populates="direccion", lazy="select")
    comuna = relationship("Comuna", back_populates="direcciones", lazy="joined")


# ============================================
# LOCALES Y CONFIGURACIÓN
# ============================================


class Local(Base):
    __tablename__ = "local"

    id = Column(Integer, primary_key=True, index=True)
    id_direccion = Column(
        Integer,
        ForeignKey("direccion.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_tipo_local = Column(
        Integer,
        ForeignKey("tipo_local.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    telefono = Column(Integer, nullable=False)
    correo = Column(String(50), nullable=False, unique=True, index=True)

    # Campos para registro de empresa
    rut_empresa = Column(String(12), unique=True, nullable=False, index=True)
    razon_social = Column(String(200), nullable=False)
    glosa_giro = Column(String(200), nullable=True)
    terminos_aceptados = Column(Boolean, nullable=False, default=False)
    fecha_aceptacion_terminos = Column(DateTime(timezone=True), nullable=True)
    version_terminos = Column(String(20), nullable=True)

    horarios = relationship(
        "Horario", back_populates="local", lazy="select", cascade="all, delete-orphan"
    )
    direccion = relationship("Direccion", back_populates="locales", lazy="joined")
    productos = relationship(
        "Producto", back_populates="local", lazy="select", cascade="all, delete-orphan"
    )
    tipo_local = relationship("TipoLocal", back_populates="locales", lazy="joined")
    redes = relationship(
        "Redes", back_populates="local", lazy="select", cascade="all, delete-orphan"
    )
    fotos = relationship(
        "Foto", back_populates="local", lazy="select", cascade="all, delete-orphan"
    )
    mesas = relationship(
        "Mesa", back_populates="local", lazy="select", cascade="all, delete-orphan"
    )
    opiniones = relationship(
        "Opinion", back_populates="local", lazy="select", cascade="all, delete-orphan"
    )
    favoritos = relationship(
        "Favorito", back_populates="local", lazy="select", cascade="all, delete-orphan"
    )
    reservas = relationship(
        "Reserva", back_populates="local", lazy="select", cascade="all, delete-orphan"
    )
    pedidos = relationship(
        "Pedido", back_populates="local", lazy="select", cascade="all, delete-orphan"
    )


class Horario(Base):
    __tablename__ = "horario"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(
        Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True
    )
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
    id_local = Column(
        Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nombre = Column(String(30), nullable=False)
    descripcion = Column(String(100), nullable=True)
    capacidad = Column(SmallInteger, nullable=False)
    orden = Column(SmallInteger, nullable=False, default=0, server_default="0")
    estado = Column(
        Enum(EstadoMesaEnum, name="estado_mesa_enum"),
        nullable=False,
        default=EstadoMesaEnum.DISPONIBLE,
    )
    eliminado_el = Column(DateTime(timezone=True), nullable=True)

    local = relationship("Local", back_populates="mesas", lazy="joined")
    reservas_mesa = relationship(
        "ReservaMesa",
        back_populates="mesa",
        lazy="select",
        cascade="all, delete-orphan",
    )
    qr_dinamicos = relationship(
        "QRDinamico", back_populates="mesa", lazy="select", cascade="all, delete-orphan"
    )
    pedidos = relationship(
        "Pedido", back_populates="mesa", lazy="select", cascade="all, delete-orphan"
    )


# ============================================
# USUARIOS Y AUTENTICACIÓN
# ============================================


class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True, index=True)
    id_rol = Column(
        Integer, ForeignKey("rol.id", ondelete="SET NULL"), nullable=True, index=True
    )
    id_local = Column(
        Integer, ForeignKey("local.id", ondelete="SET NULL"), nullable=True, index=True
    )
    nombre = Column(String(100), nullable=False)
    correo = Column(String(100), unique=True, nullable=False, index=True)
    contrasena = Column(String(200), nullable=False)
    telefono = Column(String(32), nullable=False)
    creado_el = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Campos para sistema de invitación de empleados
    invitado_por = Column(
        Integer, ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True
    )

    # Campos para términos y políticas
    terminos_aceptados = Column(Boolean, nullable=False, default=False)
    fecha_aceptacion_terminos = Column(DateTime(timezone=True), nullable=True)
    politicas_uso_aceptadas = Column(Boolean, nullable=False, default=False)
    fecha_aceptacion_politicas = Column(DateTime(timezone=True), nullable=True)

    rol = relationship("Rol", back_populates="usuarios", lazy="joined")
    local = relationship("Local", lazy="joined", foreign_keys=[id_local])
    opiniones = relationship(
        "Opinion", back_populates="usuario", lazy="select", cascade="all, delete-orphan"
    )
    favoritos = relationship(
        "Favorito",
        back_populates="usuario",
        lazy="select",
        cascade="all, delete-orphan",
    )
    reservas = relationship(
        "Reserva", back_populates="usuario", lazy="select", cascade="all, delete-orphan"
    )
    pedidos = relationship(
        "Pedido",
        back_populates="usuario",
        lazy="select",
        cascade="all, delete-orphan",
        foreign_keys="Pedido.id_usuario",
    )
    pedidos_creados = relationship(
        "Pedido",
        back_populates="creador",
        lazy="select",
        foreign_keys="Pedido.creado_por",
    )
    estados_pedido = relationship(
        "EstadoPedido", back_populates="creado_por_usuario", lazy="select"
    )
    cuentas_creadas = relationship(
        "Cuenta",
        back_populates="creador",
        lazy="select",
        foreign_keys="Cuenta.creado_por",
    )
    pagos_creados = relationship(
        "Pago", back_populates="creador", lazy="select", foreign_keys="Pago.creado_por"
    )
    qr_dinamicos = relationship(
        "QRDinamico",
        back_populates="usuario",
        lazy="select",
        cascade="all, delete-orphan",
    )


# ============================================
# SISTEMA DE INVITACIONES
# ============================================


class EstadoInvitacionEnum(str, PyEnum):
    """Estados de una invitación de empleado"""

    PENDIENTE = "pendiente"
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"
    EXPIRADA = "expirada"

    @classmethod
    def choices(cls) -> list[tuple]:
        return [
            (cls.PENDIENTE, "Pendiente"),
            (cls.ACEPTADA, "Aceptada"),
            (cls.RECHAZADA, "Rechazada"),
            (cls.EXPIRADA, "Expirada"),
        ]


class InvitacionEmpleado(Base):
    """
    Tabla para invitaciones de empleados a locales.

    Flujo:
    1. Gerente crea invitación con correo y rol
    2. Se envía email al usuario con token único
    3. Usuario acepta/rechaza la invitación
    4. Al aceptar, se convierte en empleado del local
    """

    __tablename__ = "invitacion_empleado"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(
        Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True
    )
    id_rol = Column(
        Integer, ForeignKey("rol.id", ondelete="SET NULL"), nullable=True, index=True
    )
    invitado_por = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    correo = Column(String(100), nullable=False, index=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    estado = Column(
        Enum(EstadoInvitacionEnum, name="estado_invitacion_enum"),
        nullable=False,
        default=EstadoInvitacionEnum.PENDIENTE,
    )
    creado_el = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expira_el = Column(DateTime(timezone=True), nullable=False)
    aceptado_el = Column(DateTime(timezone=True), nullable=True)
    rechazado_el = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    local = relationship("Local", lazy="joined")
    rol = relationship("Rol", lazy="joined")
    invitador = relationship("Usuario", lazy="joined", foreign_keys=[invitado_por])


# ============================================
# CONTENIDO MULTIMEDIA
# ============================================


class Foto(Base):
    __tablename__ = "foto"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(
        Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=True, index=True
    )
    id_producto = Column(
        Integer,
        ForeignKey("producto.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    id_categoria = Column(
        Integer,
        ForeignKey("categoria.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    id_tipo_foto = Column(
        Integer,
        ForeignKey("tipo_foto.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ruta = Column(
        Text, nullable=True
    )  # Para URLs externas o compatibilidad con datos antiguos
    data = Column(Text, nullable=True)  # Imagen en base64 - nuevo campo

    local = relationship("Local", back_populates="fotos", lazy="joined")
    producto = relationship("Producto", back_populates="fotos", lazy="joined")
    categoria = relationship("Categoria", back_populates="fotos", lazy="joined")
    tipo_foto = relationship("TipoFoto", back_populates="fotos", lazy="joined")
    redes = relationship("Redes", back_populates="foto", lazy="select")


class Redes(Base):
    __tablename__ = "redes"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(
        Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True
    )
    id_foto = Column(
        Integer, ForeignKey("foto.id", ondelete="SET NULL"), nullable=True, index=True
    )
    id_tipo_red = Column(
        Integer,
        ForeignKey("tipo_red.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    nombre_usuario = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)

    local = relationship("Local", back_populates="redes", lazy="joined")
    foto = relationship("Foto", back_populates="redes", lazy="joined")
    tipo_red = relationship("TipoRed", back_populates="redes", lazy="joined")


# ============================================
# CATÁLOGO DE PRODUCTOS
# ============================================


class Producto(Base):
    __tablename__ = "producto"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(
        Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True
    )
    id_categoria = Column(
        Integer,
        ForeignKey("categoria.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(500), nullable=True)
    estado = Column(
        Enum(EstadoProductoEnum, name="estado_producto_enum"),
        nullable=False,
        default=EstadoProductoEnum.DISPONIBLE,
    )
    eliminado_el = Column(DateTime(timezone=True), nullable=True)
    precio = Column(Integer, nullable=False)

    local = relationship("Local", back_populates="productos", lazy="joined")
    categoria = relationship("Categoria", back_populates="productos", lazy="joined")
    fotos = relationship(
        "Foto", back_populates="producto", lazy="select", cascade="all, delete-orphan"
    )
    cuentas = relationship("Cuenta", back_populates="producto", lazy="select")


# ============================================
# OPINIONES Y VALORACIONES
# ============================================


class Opinion(Base):
    __tablename__ = "opinion"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_local = Column(
        Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True
    )
    puntuacion = Column(Numeric(2, 1), nullable=False)
    comentario = Column(String(500), nullable=False)
    creado_el = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    eliminado_el = Column(DateTime(timezone=True), nullable=True)

    usuario = relationship("Usuario", back_populates="opiniones", lazy="joined")
    local = relationship("Local", back_populates="opiniones", lazy="joined")


# ============================================
# FAVORITOS
# ============================================


class Favorito(Base):
    __tablename__ = "favorito"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_local = Column(
        Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agregado_el = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    __table_args__ = (
        UniqueConstraint("id_usuario", "id_local", name="uq_usuario_local_favorito"),
    )

    usuario = relationship("Usuario", back_populates="favoritos", lazy="joined")
    local = relationship("Local", back_populates="favoritos", lazy="joined")


# ============================================
# RESERVAS
# ============================================


class Reserva(Base):
    __tablename__ = "reserva"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(
        Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True
    )
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fecha_reserva = Column(Date, nullable=False)
    hora_reserva = Column(Time, nullable=False)
    num_personas = Column(SmallInteger, nullable=False, default=1)
    estado = Column(
        Enum(EstadoReservaEnum, name="estado_reserva_enum"),
        nullable=False,
        default=EstadoReservaEnum.PENDIENTE,
    )
    creado_el = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    expirado_el = Column(DateTime(timezone=True), nullable=True)

    usuario = relationship("Usuario", back_populates="reservas", lazy="joined")
    local = relationship("Local", back_populates="reservas", lazy="joined")
    reservas_mesa = relationship(
        "ReservaMesa",
        back_populates="reserva",
        lazy="select",
        cascade="all, delete-orphan",
    )
    qr_dinamicos = relationship(
        "QRDinamico",
        back_populates="reserva",
        lazy="select",
        cascade="all, delete-orphan",
    )

    @property
    def prioridad(self) -> str | None:
        """Propiedad que calcula la prioridad dinamicamente"""
        return obtener_prioridad_reserva(self.fecha_reserva, self.hora_reserva)


class ReservaMesa(Base):
    __tablename__ = "reserva_mesa"

    id = Column(Integer, primary_key=True, index=False)
    id_reserva = Column(
        Integer,
        ForeignKey("reserva.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_mesa = Column(
        Integer, ForeignKey("mesa.id", ondelete="CASCADE"), nullable=False, index=True
    )

    __table_args__ = (
        UniqueConstraint("id_reserva", "id_mesa", name="uq_reserva_mesa"),
    )

    reserva = relationship("Reserva", back_populates="reservas_mesa", lazy="joined")
    mesa = relationship("Mesa", back_populates="reservas_mesa", lazy="joined")


# ============================================
# QR DINÁMICO
# ============================================


class QRDinamico(Base):
    __tablename__ = "qr_dinamico"

    id = Column(Integer, primary_key=True, index=True)
    id_mesa = Column(
        Integer, ForeignKey("mesa.id", ondelete="CASCADE"), nullable=False, index=True
    )
    id_pedido = Column(
        Integer,
        ForeignKey(
            "pedido.id",
            ondelete="CASCADE",
            use_alter=True,
            name="fk_qr_dinamico_pedido",
        ),
        nullable=True,
        index=True,
    )
    id_reserva = Column(
        Integer, ForeignKey("reserva.id", ondelete="CASCADE"), nullable=True, index=True
    )
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    codigo = Column(String(255), nullable=False, unique=True, index=True)
    expiracion = Column(DateTime(timezone=True), nullable=True)
    activo = Column(Boolean, default=True, nullable=False, index=True)
    num_personas = Column(SmallInteger, nullable=True, default=None)
    creado_el = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    mesa = relationship("Mesa", back_populates="qr_dinamicos", lazy="joined")
    pedido = relationship(
        "Pedido", foreign_keys=[id_pedido], overlaps="qr,qr_dinamicos", lazy="joined"
    )
    reserva = relationship("Reserva", back_populates="qr_dinamicos", lazy="joined")
    usuario = relationship("Usuario", back_populates="qr_dinamicos", lazy="joined")


# ============================================
# PEDIDOS Y ÓRDENES
# ============================================


class Pedido(Base):
    __tablename__ = "pedido"

    id = Column(Integer, primary_key=True, index=True)
    id_local = Column(
        Integer, ForeignKey("local.id", ondelete="CASCADE"), nullable=False, index=True
    )
    id_mesa = Column(
        Integer, ForeignKey("mesa.id", ondelete="CASCADE"), nullable=False, index=True
    )
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_qr = Column(
        Integer,
        ForeignKey(
            "qr_dinamico.id",
            ondelete="CASCADE",
            use_alter=True,
            name="fk_pedido_qr_dinamico",
        ),
        nullable=False,
        index=True,
    )
    creado_por = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    estado = Column(
        Enum(EstadoPedidoEnum, name="estado_pedido_enum"),
        nullable=False,
        default=EstadoPedidoEnum.INICIADO,
        index=True,
    )
    num_personas = Column(SmallInteger, nullable=False, default=None)
    total = Column(Integer, nullable=False, default=0)
    creado_el = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    actualizado_el = Column(DateTime(timezone=True), onupdate=func.now())
    expiracion = Column(DateTime(timezone=True), nullable=True, index=True)

    local = relationship("Local", back_populates="pedidos", lazy="joined")
    mesa = relationship("Mesa", back_populates="pedidos", lazy="joined")
    usuario = relationship(
        "Usuario",
        back_populates="pedidos",
        lazy="joined",
        foreign_keys=[id_usuario],
    )
    creador = relationship(
        "Usuario",
        back_populates="pedidos_creados",
        lazy="joined",
        foreign_keys=[creado_por],
    )
    qr = relationship(
        "QRDinamico",
        foreign_keys=[id_qr],
        overlaps="pedido,qr_dinamicos",
        lazy="joined",
    )
    cuentas = relationship(
        "Cuenta", back_populates="pedido", lazy="select", cascade="all, delete-orphan"
    )
    encomiendas = relationship(
        "Encomienda",
        back_populates="pedido",
        lazy="select",
        cascade="all, delete-orphan",
    )
    estado_pedido = relationship(
        "EstadoPedido",
        back_populates="pedido",
        lazy="select",
        cascade="all, delete-orphan",
    )
    pagos = relationship("Pago", back_populates="pedido", lazy="select")
    qr_dinamicos = relationship(
        "QRDinamico",
        foreign_keys="QRDinamico.id_pedido",
        overlaps="qr,pedido",
        lazy="select",
    )


class Cuenta(Base):
    __tablename__ = "cuenta"

    id = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(
        Integer, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False, index=True
    )
    id_producto = Column(
        Integer,
        ForeignKey("producto.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    creado_por = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cantidad = Column(Integer, nullable=False)
    observaciones = Column(String(500), nullable=True)
    creado_el = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    pedido = relationship("Pedido", back_populates="cuentas", lazy="joined")
    producto = relationship("Producto", back_populates="cuentas", lazy="joined")
    creador = relationship(
        "Usuario",
        back_populates="cuentas_creadas",
        lazy="joined",
        foreign_keys=[creado_por],
    )
    encomiendas_cuenta = relationship(
        "EncomiendaCuenta",
        back_populates="cuenta",
        lazy="select",
        cascade="all, delete-orphan",
    )


class EstadoPedido(Base):
    __tablename__ = "estado_pedido"

    id = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(
        Integer, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False, index=True
    )
    estado = Column(
        Enum(EstadoPedidoEnum, name="estado_pedido_enum"),
        nullable=False,
        index=True,
    )
    creado_por = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    creado_el = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    nota = Column(String(200), nullable=True)

    pedido = relationship("Pedido", back_populates="estado_pedido", lazy="joined")
    creado_por_usuario = relationship(
        "Usuario",
        back_populates="estados_pedido",
        lazy="joined",
        foreign_keys=[creado_por],
    )


# ============================================
# ENCOMIENDAS
# ============================================


class Encomienda(Base):
    __tablename__ = "encomienda"

    id = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(
        Integer, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False, index=True
    )
    estado = Column(
        Enum(EstadoEncomiendaEnum, name="estado_encomienda_enum"), nullable=False
    )
    creado_el = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    pedido = relationship("Pedido", back_populates="encomiendas", lazy="joined")
    cuentas_encomienda = relationship(
        "EncomiendaCuenta",
        back_populates="encomienda",
        lazy="select",
        cascade="all, delete-orphan",
    )


class EncomiendaCuenta(Base):
    __tablename__ = "encomienda_cuenta"

    id = Column(Integer, primary_key=True, index=True)
    id_cuenta = Column(
        Integer, ForeignKey("cuenta.id", ondelete="CASCADE"), nullable=False, index=True
    )
    id_encomienda = Column(
        Integer,
        ForeignKey("encomienda.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    cuenta = relationship("Cuenta", back_populates="encomiendas_cuenta", lazy="joined")
    encomienda = relationship(
        "Encomienda", back_populates="cuentas_encomienda", lazy="joined"
    )


# ============================================
# PAGOS
# ============================================


class Pago(Base):
    __tablename__ = "pago"

    id = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(
        Integer, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False, index=True
    )
    creado_por = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metodo = Column(Enum(MetodoPagoEnum, name="metodo_pago_enum"), nullable=False)
    estado = Column(
        Enum(EstadoPagoEnum, name="estado_pago_enum"),
        nullable=False,
        default=EstadoPagoEnum.PENDIENTE,
        index=True,
    )
    monto = Column(Integer, nullable=False)
    creado_el = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    actualizado_el = Column(DateTime(timezone=True), onupdate=func.now())

    pedido = relationship("Pedido", back_populates="pagos", lazy="joined")
    creador = relationship(
        "Usuario",
        back_populates="pagos_creados",
        lazy="joined",
        foreign_keys=[creado_por],
    )


# ============================================
# SCHEMAS PYDANTIC V2
# ============================================


class RolSchema(BaseModel):
    id: int | None = None
    nombre: str

    class Config:
        from_attributes = True


class UsuarioSchema(BaseModel):
    id: int | None = None
    nombre: str
    correo: EmailStr
    telefono: str | None = None
    id_rol: int | None = None

    class Config:
        from_attributes = True


class LocalSchema(BaseModel):
    id: int | None = None
    nombre: str
    telefono: int
    correo: str
    id_direccion: int
    id_tipo_local: int

    class Config:
        from_attributes = True


class ProductoSchema(BaseModel):
    id: int | None = None
    nombre: str
    descripcion: str | None = None
    precio: int
    estado: EstadoProductoEnum
    id_local: int
    id_categoria: int | None = None
    eliminado_el: datetime | None = None

    class Config:
        from_attributes = True


class PedidoSchema(BaseModel):
    id: int | None = None
    id_local: int
    id_mesa: int
    id_usuario: int
    id_qr: int
    creado_por: int
    estado: EstadoPedidoEnum
    num_personas: int | None = None
    total: int

    class Config:
        from_attributes = True


class PagoSchema(BaseModel):
    id: int | None = None
    id_pedido: int
    creado_por: int
    metodo: MetodoPagoEnum
    estado: EstadoPagoEnum
    monto: int

    class Config:
        from_attributes = True


class MesaSchema(BaseModel):
    id: int | None = None
    id_local: int
    nombre: str
    descripcion: str | None = None
    capacidad: int
    estado: EstadoMesaEnum
    eliminado_el: datetime | None = None

    class Config:
        from_attributes = True


class QRDinamicoSchema(BaseModel):
    id: int | None = None
    id_mesa: int
    id_pedido: int | None = None
    id_reserva: int | None = None
    id_usuario: int
    codigo: str
    expiracion: datetime
    activo: bool
    num_personas: int | None = None
    creado_el: datetime | None = None

    class Config:
        from_attributes = True


class ReservaSchema(BaseModel):
    id: int | None = None
    id_local: int
    id_usuario: int
    fecha_reserva: date
    hora_reserva: time
    estado: EstadoReservaEnum
    creado_el: datetime | None = None
    expirado_el: datetime | None = None
    prioridad: str | None = None  # Calculada dinámicamente

    class Config:
        from_attributes = True


class OpinionSchema(BaseModel):
    id: int | None = None
    id_usuario: int
    id_local: int
    puntuacion: float
    comentario: str
    creado_el: datetime | None = None
    eliminado_el: datetime | None = None

    class Config:
        from_attributes = True


class CuentaSchema(BaseModel):
    id: int | None = None
    id_pedido: int
    id_producto: int
    creado_por: int
    cantidad: int
    observaciones: str | None = None
    creado_el: datetime | None = None

    class Config:
        from_attributes = True


class EncomiendaSchema(BaseModel):
    id: int | None = None
    id_pedido: int
    estado: EstadoEncomiendaEnum
    creado_el: datetime | None = None

    class Config:
        from_attributes = True


class EstadoPedidoSchema(BaseModel):
    id: int | None = None
    id_pedido: int
    estado: EstadoPedidoEnum
    creado_por: int
    creado_el: datetime | None = None
    nota: str | None = None

    class Config:
        from_attributes = True
