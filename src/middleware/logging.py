"""
Middleware para logging de requests HTTP.

Registra información de cada request y response para debugging y auditoría.
"""

import logging
import time

from flask import g, request

logger = logging.getLogger(__name__)


def setup_request_logging(app):
    """
    Configura logging de requests en la aplicación Flask.

    Args:
        app: Instancia de Flask
    """

    @app.before_request
    def log_request_info():
        """Log de información antes de procesar el request"""
        g.request_start_time = time.time()

        # Log básico del request
        logger.info(
            f"→ {request.method} {request.path} "
            f"from {request.remote_addr} "
            f"({request.user_agent.string[:50]}...)"
        )

        # Log de query params si existen
        if request.args:
            logger.debug(f"  Query params: {dict(request.args)}")

        # Log de request ID si existe (del middleware request_id)
        request_id = getattr(g, "request_id", None)
        if request_id:
            logger.debug(f"  Request ID: {request_id}")

    @app.after_request
    def log_response_info(response):
        """Log de información después de procesar el request"""
        # Calcular tiempo de procesamiento
        if hasattr(g, "request_start_time"):
            elapsed_time = time.time() - g.request_start_time
            elapsed_ms = int(elapsed_time * 1000)
        else:
            elapsed_ms = 0

        # Log de respuesta
        logger.info(
            f"← {request.method} {request.path} "
            f"returned {response.status_code} "
            f"in {elapsed_ms}ms"
        )

        # Log de errores
        if response.status_code >= 400:
            logger.warning(f"  Error response: {response.status_code}")

        return response
