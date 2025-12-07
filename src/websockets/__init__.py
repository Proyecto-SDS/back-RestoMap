"""WebSockets para comunicacion en tiempo real."""

from flask_socketio import SocketIO, emit, join_room, leave_room

# Instancia global de SocketIO
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")


def init_socketio(app):
    """Inicializa SocketIO con la aplicacion Flask."""
    socketio.init_app(app)
    register_handlers()
    return socketio


def register_handlers():
    """Registra los handlers de eventos WebSocket."""

    @socketio.on("connect")
    def handle_connect():
        """Cliente conectado."""
        print("[WS] Cliente conectado")
        emit("connected", {"status": "ok"})

    @socketio.on("disconnect")
    def handle_disconnect():
        """Cliente desconectado."""
        print("[WS] Cliente desconectado")

    @socketio.on("join_local")
    def handle_join_local(data):
        """Unirse a la sala del local para recibir actualizaciones."""
        local_id = data.get("local_id")
        if local_id:
            room = f"local_{local_id}"
            join_room(room)
            print(f"[WS] Usuario unido a sala: {room}")
            emit("joined", {"room": room})

    @socketio.on("join_mesa")
    def handle_join_mesa(data):
        """Unirse a la sala de una mesa especifica."""
        mesa_id = data.get("mesa_id")
        if mesa_id:
            room = f"mesa_{mesa_id}"
            join_room(room)
            print(f"[WS] Usuario unido a sala: {room}")
            emit("joined", {"room": room})

    @socketio.on("join_pedido")
    def handle_join_pedido(data):
        """Unirse a la sala de un pedido especifico."""
        pedido_id = data.get("pedido_id")
        if pedido_id:
            room = f"pedido_{pedido_id}"
            join_room(room)
            print(f"[WS] Usuario unido a sala: {room}")
            emit("joined", {"room": room})

    @socketio.on("leave_room")
    def handle_leave_room(data):
        """Salir de una sala."""
        room = data.get("room")
        if room:
            leave_room(room)
            print(f"[WS] Usuario salio de sala: {room}")


# ============================================
# Funciones para emitir eventos desde el backend
# ============================================


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
