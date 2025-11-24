from enum import Enum
# basados en la base de datos

class MetodoPago(str, Enum):
    efectivo = "efectivo"
    transferencia = "transferencia"
    debito = "debito"
    credito = "credito"
    app_de_pago = "app_de_pago"
    otro = "otro"

class EstadoPago(str, Enum):
    pendiente = "pendiente"
    cobrado = "cobrado"
    cancelado = "cancelado"

class EstadoPedido(str, Enum):
    abierto = "abierto"
    en_preparacion = "en_preparacion"
    listo = "listo"
    entregado = "entregado"
    cerrado = "cerrado"
    cancelado = "cancelado"

class EstadoMesa(str, Enum):
    disponible = "disponible"
    reservada = "reservada"
    ocupada = "ocupada"
    fuera_de_servicio = "fuera_de_servicio"

class EstadoReserva(str, Enum):
    pendiente = "pendiente"
    confirmada = "confirmada"
    rechazada = "rechazada"

class EstadoEncomienda(str, Enum):
    pendiente = "pendiente"
    en_preparacion = "en_preparacion"
    lista = "lista"
    entregada = "entregada"
    cancelada = "cancelada"

class ProductoEstado(str, Enum):
    disponible = "disponible"
    agotado = "agotado"
    inactivo = "inactivo"