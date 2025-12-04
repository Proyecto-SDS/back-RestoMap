"""
Modulo de modelos SQLAlchemy y Schemas Pydantic
Exporta todos los modelos, schemas y enums para facilitar importaciones
"""

from .models import (
    # ============ Base ============
    Base,
    Categoria,
    Comuna,
    Cuenta,
    CuentaSchema,
    # ============ Modelos - Ubicacion ============
    Direccion,
    # ============ Modelos - Encomiendas ============
    Encomienda,
    EncomiendaCuenta,
    EncomiendaSchema,
    EstadoEncomiendaEnum,
    EstadoMesaEnum,
    EstadoPagoEnum,
    EstadoPedido,
    EstadoPedidoEnum,
    EstadoProductoEnum,
    EstadoReservaEnum,
    Favorito,
    # ============ Modelos - Multimedia ============
    Foto,
    Horario,
    # ============ Modelos - Locales ============
    Local,
    LocalSchema,
    Mesa,
    MesaSchema,
    # ============ Enums ============
    MetodoPagoEnum,
    # ============ Modelos - Opiniones ============
    Opinion,
    OpinionSchema,
    # ============ Modelos - Pagos ============
    Pago,
    PagoSchema,
    # ============ Modelos - Pedidos ============
    Pedido,
    PedidoSchema,
    # ============ Modelos - Productos ============
    Producto,
    ProductoSchema,
    # ============ Modelos - QR ============
    QRDinamico,
    QRDinamicoSchema,
    Redes,
    # ============ Modelos - Reservas ============
    Reserva,
    ReservaMesa,
    ReservaSchema,
    # ============ Modelos - Tablas de Referencia ============
    Rol,
    RolEnum,
    # ============ Schemas Pydantic ============
    RolSchema,
    TipoFoto,
    TipoHorarioEnum,
    TipoLocal,
    TipoRed,
    # ============ Modelos - Usuarios ============
    Usuario,
    UsuarioSchema,
    # ============ Funciones Auxiliares ============
    obtener_etiqueta,
    validar_transicion_estado,
)

__all__ = [
    # Base
    "Base",
    "Categoria",
    "Comuna",
    "Cuenta",
    "CuentaSchema",
    # Modelos - Ubicacion
    "Direccion",
    # Modelos - Encomiendas
    "Encomienda",
    "EncomiendaCuenta",
    "EncomiendaSchema",
    "EstadoEncomiendaEnum",
    "EstadoMesaEnum",
    "EstadoPagoEnum",
    "EstadoPedido",
    "EstadoPedidoEnum",
    "EstadoProductoEnum",
    "EstadoReservaEnum",
    "Favorito",
    # Modelos - Multimedia
    "Foto",
    "Horario",
    # Modelos - Locales
    "Local",
    "LocalSchema",
    "Mesa",
    "MesaSchema",
    # Enums
    "MetodoPagoEnum",
    # Modelos - Opiniones
    "Opinion",
    "OpinionSchema",
    # Modelos - Pagos
    "Pago",
    "PagoSchema",
    # Modelos - Pedidos
    "Pedido",
    "PedidoSchema",
    # Modelos - Productos
    "Producto",
    "ProductoSchema",
    # Modelos - QR
    "QRDinamico",
    "QRDinamicoSchema",
    "Redes",
    # Modelos - Reservas
    "Reserva",
    "ReservaMesa",
    "ReservaSchema",
    # Modelos - Referencia
    "Rol",
    "RolEnum",
    # Schemas Pydantic
    "RolSchema",
    "TipoFoto",
    "TipoHorarioEnum",
    "TipoLocal",
    "TipoRed",
    # Modelos - Usuarios
    "Usuario",
    "UsuarioSchema",
    # Funciones Auxiliares
    "obtener_etiqueta",
    "validar_transicion_estado",
]
