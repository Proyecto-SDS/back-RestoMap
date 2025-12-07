"""Configuracion central de SocketIO."""

from flask_socketio import SocketIO

# Instancia global de SocketIO
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")


def init_socketio(app):
    """Inicializa SocketIO con la aplicacion Flask."""
    socketio.init_app(app)
    # Importar handlers para registrarlos (decorators)
    from . import handlers  # noqa: F401

    return socketio
