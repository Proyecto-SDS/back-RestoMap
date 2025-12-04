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
    EstadoPedidoSchema,
    EstadoProductoEnum,
    EstadoReservaEnum,
    # ============ Modelos - Favoritos ============
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
    # ============ Tablas de Referencia ============
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
    obtener_prioridad_reserva,
    validar_transicion_estado,
)

__all__ = [  # noqa: RUF022
    # Base
    "Base",
    # Tablas de Referencia
    "Rol",
    "Comuna",
    "TipoLocal",
    "TipoRed",
    "TipoFoto",
    "Categoria",
    # Modelos - Ubicacion
    "Direccion",
    # Modelos - Locales
    "Local",
    "Horario",
    "Mesa",
    # Modelos - Usuarios
    "Usuario",
    # Modelos - Multimedia
    "Foto",
    "Redes",
    # Modelos - Productos
    "Producto",
    # Modelos - Opiniones
    "Opinion",
    # Modelos - Favoritos
    "Favorito",
    # Modelos - Reservas
    "Reserva",
    "ReservaMesa",
    # Modelos - QR
    "QRDinamico",
    # Modelos - Pedidos
    "Pedido",
    "Cuenta",
    "EstadoPedido",
    # Modelos - Encomiendas
    "Encomienda",
    "EncomiendaCuenta",
    # Modelos - Pagos
    "Pago",
    # Enums
    "MetodoPagoEnum",
    "EstadoPagoEnum",
    "EstadoPedidoEnum",
    "EstadoMesaEnum",
    "EstadoReservaEnum",
    "EstadoProductoEnum",
    "EstadoEncomiendaEnum",
    "RolEnum",
    "TipoHorarioEnum",
    # Schemas Pydantic
    "RolSchema",
    "UsuarioSchema",
    "LocalSchema",
    "ProductoSchema",
    "PedidoSchema",
    "PagoSchema",
    "MesaSchema",
    "QRDinamicoSchema",
    "ReservaSchema",
    "OpinionSchema",
    "CuentaSchema",
    "EncomiendaSchema",
    "EstadoPedidoSchema",
    # Funciones Auxiliares
    "obtener_etiqueta",
    "obtener_prioridad_reserva",
    "validar_transicion_estado",
]
