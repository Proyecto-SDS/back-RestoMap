"""
WebSockets para comunicacion en tiempo real.

Este paquete proporciona:
- Handlers de eventos WebSocket (connect, disconnect, join_*, leave_room)
- Funciones emit_* para enviar eventos desde el backend
- Configuracion de SocketIO

Uso:
    from websockets import init_socketio, socketio
    from websockets import emit_qr_escaneado, emit_estado_pedido
"""

# Core
from .core import init_socketio, socketio

# Emitters (funciones para enviar eventos)
from .emitters import (
    emit_estado_encomienda,
    emit_estado_pedido,
    emit_mesa_actualizada,
    emit_nueva_encomienda,
    emit_nueva_reserva,
    emit_nuevo_pedido,
    emit_producto_actualizado,
    emit_qr_escaneado,
    emit_reserva_actualizada,
)

__all__ = [
    "emit_estado_encomienda",
    "emit_estado_pedido",
    "emit_mesa_actualizada",
    "emit_nueva_encomienda",
    "emit_nueva_reserva",
    "emit_nuevo_pedido",
    "emit_producto_actualizado",
    "emit_qr_escaneado",
    "emit_reserva_actualizada",
    "init_socketio",
    "socketio",
]
