"""
Middleware para manejo centralizado de errores.

Captura excepciones personalizadas y las convierte en respuestas JSON apropiadas.
"""

import traceback

from flask import jsonify

from config import get_logger
from exceptions import AppError, HTTPError

logger = get_logger(__name__)


def register_error_handlers(app):
    """
    Registra los manejadores de error en la aplicación Flask.

    Args:
        app: Instancia de Flask
    """

    @app.errorhandler(HTTPError)
    def handle_http_exception(error):
        """Maneja excepciones HTTP personalizadas"""
        logger.warning(f"HTTP Exception: {error.message} (Status: {error.status_code})")

        response = {
            "success": False,
            "error": error.message,
            "status_code": error.status_code,
        }

        # Agregar detalles si existen
        if error.details:
            response["details"] = error.details

        return jsonify(response), error.status_code

    @app.errorhandler(AppError)
    def handle_app_exception(error):
        """Maneja excepciones de aplicación genéricas"""
        logger.error(f"App Exception: {error.message}")

        response = {
            "success": False,
            "error": error.message,
        }

        if error.details:
            response["details"] = error.details

        return jsonify(response), 500

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        """Maneja errores de validación de Python"""
        logger.warning(f"ValueError: {error!s}")
        return jsonify({"success": False, "error": str(error)}), 400

    @app.errorhandler(404)
    def handle_404(_error):
        """Maneja error 404 - Ruta no encontrada"""
        return jsonify({"success": False, "error": "Ruta no encontrada"}), 404

    @app.errorhandler(405)
    def handle_405(_error):
        """Maneja error 405 - Método no permitido"""
        return jsonify({"success": False, "error": "Método HTTP no permitido"}), 405

    @app.errorhandler(500)
    def handle_500(error):
        """Maneja error 500 - Error interno del servidor"""
        logger.error(f"Internal Server Error: {error!s}")
        logger.error(traceback.format_exc())

        return (
            jsonify(
                {
                    "success": False,
                    "error": "Error interno del servidor",
                }
            ),
            500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Maneja excepciones no capturadas"""
        logger.critical(f"Unexpected error: {error!s}")
        logger.critical(traceback.format_exc())

        return (
            jsonify(
                {
                    "success": False,
                    "error": "Error inesperado del servidor",
                }
            ),
            500,
        )
