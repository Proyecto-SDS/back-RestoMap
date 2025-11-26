"""
Módulo de modelos SQLAlchemy y Schemas Pydantic
Exporta todos los modelos, schemas y enums para facilitar importaciones
"""

from .models import (
    # ============ Base ============
    Base,
    
    # ============ Enums ============
    MetodoPagoEnum,
    EstadoPagoEnum,
    EstadoPedidoEnum,
    EstadoMesaEnum,
    EstadoReservaEnum,
    EstadoReservaMesaEnum,
    EstadoProductoEnum,
    EstadoEncomiendaEnum,
    RolEnum,
    TipoHorarioEnum,
    
    # ============ Modelos - Tablas de Referencia ============
    Rol,
    Comuna,
    TipoLocal,
    TipoRed,
    TipoFoto,
    Categoria,
    
    # ============ Modelos - Ubicación ============
    Direccion,
    
    # ============ Modelos - Locales ============
    Local,
    Horario,
    Mesa,
    
    # ============ Modelos - Usuarios ============
    Usuario,
    
    # ============ Modelos - Multimedia ============
    Foto,
    Redes,
    
    # ============ Modelos - Productos ============
    Producto,
    
    # ============ Modelos - Opiniones ============
    Opinion,
    Favorito,
    
    # ============ Modelos - Reservas ============
    Reserva,
    ReservaMesa,
    
    # ============ Modelos - Pedidos ============
    Pedido,
    Cuenta,
    EstadoPedido,
    
    # ============ Modelos - QR ============
    QRDinamico,
    
    # ============ Modelos - Encomiendas ============
    Encomienda,
    EncomiendaCuenta,
    
    # ============ Modelos - Pagos ============
    Pago,
    
    # ============ Schemas Pydantic ============
    RolSchema,
    UsuarioSchema,
    LocalSchema,
    ProductoSchema,
    PedidoSchema,
    PagoSchema,
    MesaSchema,
    QRDinamicoSchema,
    ReservaSchema,
    OpinionSchema,
    CuentaSchema,
    EncomiendaSchema,
    
    # ============ Funciones Auxiliares ============
    obtener_etiqueta,
    obtener_colores_estado,
    validar_transicion_estado,
)

__all__ = [
    # Base
    "Base",
    
    # Enums
    "MetodoPagoEnum",
    "EstadoPagoEnum",
    "EstadoPedidoEnum",
    "EstadoMesaEnum",
    "EstadoReservaEnum",
    "EstadoReservaMesaEnum",
    "EstadoProductoEnum",
    "EstadoEncomiendaEnum",
    "RolEnum",
    "TipoHorarioEnum",
    
    # Modelos - Referencia
    "Rol",
    "Comuna",
    "TipoLocal",
    "TipoRed",
    "TipoFoto",
    "Categoria",
    
    # Modelos - Ubicación
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
    "Favorito",
    
    # Modelos - Reservas
    "Reserva",
    "ReservaMesa",
    
    # Modelos - Pedidos
    "Pedido",
    "Cuenta",
    "EstadoPedido",
    
    # Modelos - QR
    "QRDinamico",
    
    # Modelos - Encomiendas
    "Encomienda",
    "EncomiendaCuenta",
    
    # Modelos - Pagos
    "Pago",
    
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
    
    # Funciones Auxiliares
    "obtener_etiqueta",
    "obtener_colores_estado",
    "validar_transicion_estado",
]
