"""Handlers de eventos WebSocket."""

from flask_socketio import emit, join_room, leave_room

from config import get_logger

from .core import socketio

logger = get_logger(__name__)

# Colores ANSI
GREEN = "\033[32m"
RED = "\033[31m"
BLUE = "\033[34m"
RESET = "\033[0m"


@socketio.on("connect")
def handle_connect():
    """Cliente conectado."""
    logger.info(f"Cliente {GREEN}conectado{RESET}")
    emit("connected", {"status": "ok"})


@socketio.on("disconnect")
def handle_disconnect(*args):
    """Cliente desconectado."""
    razon = args[0] if args else "desconocida"
    logger.info(f"Cliente {RED}desconectado{RESET}. Razon: {razon}")


@socketio.on("join_local")
def handle_join_local(data):
    """Unirse a la sala del local para recibir actualizaciones."""
    local_id = data.get("local_id")
    if local_id:
        room = f"local_{local_id}"
        join_room(room)
        logger.debug(f"Usuario {GREEN}unido{RESET} a sala: {BLUE}{room}{RESET}")
        emit("joined", {"room": room})


@socketio.on("join_mesa")
def handle_join_mesa(data):
    """Unirse a la sala de una mesa especifica."""
    mesa_id = data.get("mesa_id")
    if mesa_id:
        room = f"mesa_{mesa_id}"
        join_room(room)
        logger.debug(f"Usuario {GREEN}unido{RESET} a sala: {BLUE}{room}{RESET}")
        emit("joined", {"room": room})


@socketio.on("join_pedido")
def handle_join_pedido(data):
    """Unirse a la sala de un pedido especifico."""
    pedido_id = data.get("pedido_id")
    if pedido_id:
        room = f"pedido_{pedido_id}"
        join_room(room)
        logger.debug(f"Usuario {GREEN}unido{RESET} a sala: {BLUE}{room}{RESET}")
        emit("joined", {"room": room})


@socketio.on("leave_room")
def handle_leave_room(data):
    """Salir de una sala."""
    room = data.get("room")
    if room:
        leave_room(room)
        logger.debug(f"Usuario {RED}salio{RESET} de sala: {BLUE}{room}{RESET}")
