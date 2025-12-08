"""
Punto de entrada principal de la aplicacion Flask
Backend - Sistema de Gestion de Locales
"""

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config, get_logger, setup_logging
from database import db_session
from middleware import register_middleware
from websockets import init_socketio, socketio

# Configurar logging centralizado
setup_logging()
logger = get_logger(__name__)


def create_app(config: Config | None = None) -> Flask:
    """
    Factory function para crear la aplicacion Flask

    Args:
        config: Objeto de configuracion opcional (útil para testing)

    Returns:
        Instancia configurada de Flask
    """
    app = Flask(__name__)

    # Usar configuracion proporcionada o la predeterminada
    if config is None:
        config = Config()

    # Validar configuracion
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Error de configuracion: {e}")
        raise

    # Aplicar configuracion
    app.config.from_object(config)

    # Configurar CORS
    _configure_cors(app, config.ALLOWED_ORIGINS)

    # Configurar manejo de base de datos
    _configure_database(app)

    # Registrar middleware (error handlers, logging, request ID)
    register_middleware(app)

    # Registrar blueprints
    _register_blueprints(app)

    # Rutas básicas
    _register_basic_routes(app)

    logger.info("Aplicacion Flask creada correctamente")
    logger.info(f"Entorno: {config.ENV}")
    logger.info(f"Debug: {config.DEBUG}")
    logger.info(f"CORS permitido desde: {', '.join(config.ALLOWED_ORIGINS)}")

    # Inicializar WebSockets
    init_socketio(app)
    logger.info("WebSockets (Flask-SocketIO) inicializado")

    return app


def _configure_cors(app: Flask, allowed_origins: list[str]) -> None:
    """Configura CORS para la aplicacion"""
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
                "allow_headers": ["Content-Type", "Authorization"],
                "expose_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
                "max_age": 3600,  # Cache preflight por 1 hora
            }
        },
    )
    logger.info(f"CORS configurado para {len(allowed_origins)} origen(es)")


def _configure_database(app: Flask) -> None:
    """Configura el manejo de sesiones de base de datos"""

    @app.teardown_appcontext
    def shutdown_session(exception: BaseException | None = None) -> None:
        """Cierra la sesion de base de datos al final de cada request"""
        db_session.remove()
        if exception:
            logger.error(f"Error en request: {exception}")

    logger.info("Manejo de sesiones de BD configurado")


def _register_error_handlers(app: Flask) -> None:
    """Registra manejadores de errores globales"""

    @app.errorhandler(404)
    def not_found(_error):
        """Maneja errores 404 - Recurso no encontrado"""
        return jsonify(
            {
                "error": "Recurso no encontrado",
                "message": "La ruta solicitada no existe",
                "status": 404,
            }
        ), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Maneja errores 500 - Error interno del servidor"""
        logger.error(f"Error interno del servidor: {error}")
        db_session.rollback()  # Rollback en caso de error
        return jsonify(
            {
                "error": "Error interno del servidor",
                "message": "Ocurrio un error procesando la solicitud",
                "status": 500,
            }
        ), 500

    @app.errorhandler(403)
    def forbidden(_error):
        """Maneja errores 403 - Prohibido"""
        return jsonify(
            {
                "error": "Acceso prohibido",
                "message": "No tiene permisos para acceder a este recurso",
                "status": 403,
            }
        ), 403

    @app.errorhandler(401)
    def unauthorized(_error):
        """Maneja errores 401 - No autorizado"""
        return jsonify(
            {
                "error": "No autorizado",
                "message": "Debe autenticarse para acceder a este recurso",
                "status": 401,
            }
        ), 401

    @app.errorhandler(400)
    def bad_request(error):
        """Maneja errores 400 - Solicitud incorrecta"""
        return jsonify(
            {
                "error": "Solicitud incorrecta",
                "message": str(error)
                if str(error)
                != "400 Bad Request: The browser (or proxy) sent a request that this server could not understand."
                else "La solicitud contiene datos inválidos",
                "status": 400,
            }
        ), 400

    logger.info("Error handlers registrados (400, 401, 403, 404, 500)")


def _register_blueprints(app: Flask) -> None:
    """Registra todos los blueprints de la aplicacion"""

    # Importar blueprints
    from routes import locales_bp
    from routes.auth import auth_bp
    from routes.cliente import cliente_bp
    from routes.empresa import empresa_bp
    from routes.favoritos import favoritos_bp
    from routes.invitaciones import invitaciones_bp
    from routes.opiniones import opiniones_bp
    from routes.reservas import reservas_bp

    # Registrar blueprints
    blueprints = [
        (locales_bp, "locales"),
        (auth_bp, "auth"),
        (opiniones_bp, "opiniones"),
        (reservas_bp, "reservas"),
        (favoritos_bp, "favoritos"),
        (empresa_bp, "empresa"),
        (invitaciones_bp, "invitaciones"),
        (cliente_bp, "cliente"),
    ]

    for blueprint, name in blueprints:
        app.register_blueprint(blueprint)
        logger.info(f"  Blueprint '{name}' registrado")

    logger.info(f"{len(blueprints)} blueprints registrados")


def _register_basic_routes(app: Flask) -> None:
    """Registra rutas básicas como health check"""

    @app.route("/")
    def index():
        """Ruta raiz - Redirige a health check"""
        return health_check()

    @app.route("/health")
    @app.route("/api/health")
    def health_check():
        """
        Health check endpoint para monitoreo

        Returns:
            JSON con estado del servidor
        """
        return jsonify(
            {
                "status": "ok",
                "message": "Backend Flask funcionando correctamente",
                "environment": app.config.get("ENV", "unknown"),
                "version": "1.0.0",  # Considera usar un archivo VERSION
            }
        ), 200

    @app.route("/api")
    def api_info():
        """Informacion de la API"""
        return jsonify(
            {
                "name": "Sistema de Gestion de Locales - API",
                "version": "1.0.0",
                "endpoints": {
                    "health": "/health",
                    "auth": "/api/auth",
                    "locales": "/api/locales",
                    "opiniones": "/api/opiniones",
                    "reservas": "/api/reservas",
                    "favoritos": "/api/favoritos",
                    "empresa": "/api/empresa",
                },
                "documentation": "Ver README.md para documentacion completa",
            }
        ), 200

    logger.info("Rutas básicas registradas (/health, /api)")


# Crear instancia de la aplicacion
app = create_app()

if __name__ == "__main__":
    """
    Punto de entrada cuando se ejecuta directamente

    Nota: En produccion, usar Gunicorn en lugar de app.run()
    Ejemplo: gunicorn -w 4 -b 0.0.0.0:5000 main:app
    """

    logger.info("=" * 60)
    logger.info("Iniciando servidor Flask de desarrollo")
    logger.info("=" * 60)
    logger.info(f"Puerto: {Config.PORT}")
    logger.info(f"Modo debug: {Config.DEBUG}")
    logger.info(f"Entorno: {Config.ENV}")
    logger.info("=" * 60)

    if Config.ENV == "production":
        logger.warning("Ejecutando Flask development server en produccion.")
        logger.warning("Se recomienda usar Gunicorn o uWSGI en produccion.")

    # Ejecutar servidor con SocketIO
    # log_output=False evita logs duplicados de werkzeug (ya usamos middleware.logging)
    socketio.run(
        app,
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG,
        use_reloader=Config.DEBUG,
        log_output=False,
    )
