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
