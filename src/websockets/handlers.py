"""Handlers de eventos WebSocket."""

from flask import request
from flask_socketio import emit, join_room, leave_room

from config import get_logger

from .core import socketio

logger = get_logger(__name__)

# Colores ANSI
GREEN = "\033[32m"
RED = "\033[31m"
BLUE = "\033[34m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RESET = "\033[0m"

# Dict para guardar info de usuarios conectados por socket id
connected_users: dict[str, dict] = {}


def get_user_info(sid: str | None = None) -> str:
    """Obtiene la info formateada del usuario conectado."""
    socket_id = sid or request.sid  # type: ignore  # Flask-SocketIO adds sid dynamically
    user = connected_users.get(socket_id)
    if user:
        return f"{CYAN}{user['nombre']}{RESET} ({YELLOW}{user['rol']}{RESET})"
    return "Usuario anonimo"


@socketio.on("connect")
def handle_connect():
    """Cliente conectado."""
    logger.info(f"Cliente {GREEN}conectado{RESET} (sid: {request.sid[:8]}...)")  # type: ignore
    emit("connected", {"status": "ok"})


@socketio.on("disconnect")
def handle_disconnect(*args):
    """Cliente desconectado."""
    razon = args[0] if args else "desconocida"
    user_info = get_user_info()
    # Limpiar usuario del dict
    if request.sid in connected_users:  # type: ignore
        del connected_users[request.sid]  # type: ignore
    logger.info(f"{user_info} {RED}desconectado{RESET}. Razon: {razon}")


@socketio.on("authenticate")
def handle_authenticate(data):
    """Recibe datos del usuario para identificacion en logs."""
    user_id = data.get("user_id")
    nombre = data.get("nombre", "Sin nombre")
    rol = data.get("rol", "desconocido")

    connected_users[request.sid] = {  # type: ignore
        "user_id": user_id,
        "nombre": nombre,
        "rol": rol,
    }

    logger.info(
        f"Usuario autenticado: {CYAN}{nombre}{RESET} "
        f"(id: {user_id}, rol: {YELLOW}{rol}{RESET})"
    )
    emit("authenticated", {"status": "ok"})


@socketio.on("join_local")
def handle_join_local(data):
    """Unirse a la sala del local para recibir actualizaciones."""
    local_id = data.get("local_id")
    if local_id:
        room = f"local_{local_id}"
        join_room(room)
        user_info = get_user_info()
        logger.debug(f"{user_info} {GREEN}unido{RESET} a sala: {BLUE}{room}{RESET}")
        emit("joined", {"room": room})


@socketio.on("join_mesa")
def handle_join_mesa(data):
    """Unirse a la sala de una mesa especifica."""
    mesa_id = data.get("mesa_id")
    if mesa_id:
        room = f"mesa_{mesa_id}"
        join_room(room)
        user_info = get_user_info()
        logger.debug(f"{user_info} {GREEN}unido{RESET} a sala: {BLUE}{room}{RESET}")
        emit("joined", {"room": room})


@socketio.on("join_pedido")
def handle_join_pedido(data):
    """Unirse a la sala de un pedido especifico."""
    pedido_id = data.get("pedido_id")
    if pedido_id:
        room = f"pedido_{pedido_id}"
        join_room(room)
        user_info = get_user_info()
        logger.debug(f"{user_info} {GREEN}unido{RESET} a sala: {BLUE}{room}{RESET}")
        emit("joined", {"room": room})


@socketio.on("leave_room")
def handle_leave_room(data):
    """Salir de una sala."""
    room = data.get("room")
    if room:
        leave_room(room)
        user_info = get_user_info()
        logger.debug(f"{user_info} {RED}salio{RESET} de sala: {BLUE}{room}{RESET}")
