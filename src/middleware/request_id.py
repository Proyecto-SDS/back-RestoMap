"""
Middleware para generar Request IDs únicos.

Genera un ID único para cada request para facilitar trazabilidad y debugging.
"""

import uuid

from flask import g, request


def setup_request_id(app):
    """
    Configura generación de Request IDs en la aplicación Flask.

    Args:
        app: Instancia de Flask
    """

    @app.before_request
    def generate_request_id():
        """Genera un ID único para cada request"""
        # Intentar obtener del header si existe (útil para clientes que envían su propio ID)
        request_id = request.headers.get("X-Request-ID")

        # Si no existe, generar uno nuevo
        if not request_id:
            request_id = str(uuid.uuid4())

        # Guardar en el contexto global de Flask
        g.request_id = request_id

    @app.after_request
    def add_request_id_header(response):
        """Agrega el Request ID al header de respuesta"""
        if hasattr(g, "request_id"):
            response.headers["X-Request-ID"] = g.request_id

        return response
