"""Funciones para emitir eventos WebSocket desde el backend."""

from .core import socketio


def emit_qr_escaneado(local_id: int, mesa_id: int, pedido_id: int):
    """Notifica que un cliente escaneo un QR."""
    socketio.emit(
        "qr_escaneado",
        {"mesa_id": mesa_id, "pedido_id": pedido_id},
        room=f"local_{local_id}",
    )


def emit_nuevo_pedido(local_id: int, pedido_data: dict):
    """Notifica que hay un nuevo pedido."""
    socketio.emit(
        "nuevo_pedido",
        pedido_data,
        room=f"local_{local_id}",
    )


def emit_nueva_encomienda(local_id: int, encomienda_data: dict):
    """Notifica que hay una nueva encomienda para preparar."""
    socketio.emit(
        "nueva_encomienda",
        encomienda_data,
        room=f"local_{local_id}",
    )


def emit_estado_encomienda(
    local_id: int, pedido_id: int, encomienda_id: int, estado: str
):
    """Notifica cambio de estado de encomienda."""
    data = {"encomienda_id": encomienda_id, "estado": estado}
    # Notificar al local (empleados)
    socketio.emit("estado_encomienda", data, room=f"local_{local_id}")
    # Notificar al pedido especifico (cliente)
    socketio.emit("estado_encomienda", data, room=f"pedido_{pedido_id}")


def emit_estado_pedido(local_id: int, pedido_id: int, estado: str):
    """Notifica cambio de estado del pedido."""
    data = {"pedido_id": pedido_id, "estado": estado}
    socketio.emit("estado_pedido", data, room=f"local_{local_id}")
    socketio.emit("estado_pedido", data, room=f"pedido_{pedido_id}")


def emit_mesa_actualizada(local_id: int, mesa_id: int, estado: str):
    """Notifica que el estado de una mesa cambio."""
    socketio.emit(
        "mesa_actualizada",
        {"mesa_id": mesa_id, "estado": estado},
        room=f"local_{local_id}",
    )


def emit_expiracion_actualizada(
    local_id: int, mesa_id: int, nueva_expiracion: str | None
):
    """Notifica que la expiración de un pedido/mesa cambió."""
    socketio.emit(
        "expiracion_actualizada",
        {"mesa_id": mesa_id, "expiracion": nueva_expiracion},
        room=f"local_{local_id}",
    )


def emit_nueva_reserva(local_id: int, reserva_data: dict):
    """Notifica que hay una nueva reserva."""
    socketio.emit(
        "nueva_reserva",
        reserva_data,
        room=f"local_{local_id}",
    )


def emit_reserva_actualizada(local_id: int, reserva_data: dict):
    """Notifica cambio de estado en una reserva."""
    socketio.emit(
        "reserva_actualizada",
        reserva_data,
        room=f"local_{local_id}",
    )


def emit_producto_actualizado(local_id: int, producto_data: dict):
    """Notifica cambio en un producto (stock, precio, estado)."""
    socketio.emit(
        "producto_actualizado",
        producto_data,
        room=f"local_{local_id}",
    )


# ============================================
# ALERTAS DE PEDIDOS - SISTEMA DE EXPIRACION
# ============================================


def emit_alerta_pedido(
    local_id: int,
    pedido_id: int,
    mesa_id: int,
    mesa_nombre: str,
    tipo_alerta: str,
    mensaje: str,
    minutos_restantes: int | None = None,
):
    """
    Alerta para mesero sobre estado de pedido.

    tipo_alerta: 'terminado_5min', 'terminado_10min',
                 'servido_15min', 'servido_10min', 'servido_5min'
    """
    socketio.emit(
        "alerta_pedido",
        {
            "pedido_id": pedido_id,
            "mesa_id": mesa_id,
            "mesa_nombre": mesa_nombre,
            "tipo_alerta": tipo_alerta,
            "mensaje": mensaje,
            "minutos_restantes": minutos_restantes,
        },
        room=f"local_{local_id}",
    )


def emit_pedido_expirado(local_id: int, pedido_id: int, mesa_id: int, mesa_nombre: str):
    """Notifica que un pedido expiró y fue cancelado automáticamente."""
    socketio.emit(
        "pedido_expirado",
        {
            "pedido_id": pedido_id,
            "mesa_id": mesa_id,
            "mesa_nombre": mesa_nombre,
        },
        room=f"local_{local_id}",
    )


def emit_urgencia_kanban(
    local_id: int, pedido_id: int, mesa_nombre: str, minutos_espera: int
):
    """Alerta de urgencia para Kanban - pedido >30min en RECEPCION."""
    socketio.emit(
        "urgencia_kanban",
        {
            "pedido_id": pedido_id,
            "mesa_nombre": mesa_nombre,
            "minutos_espera": minutos_espera,
        },
        room=f"local_{local_id}",
    )
