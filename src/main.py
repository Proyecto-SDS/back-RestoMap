"""
Punto de entrada principal de la aplicacion Flask - VERSION BLINDADA PARA CLOUD RUN
"""
import sys
import os
import time
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

# --- 1. IMPORTACIONES PROTEGIDAS ---
# Envolvemos las dependencias críticas para que si fallan, la app no muera (exit 2)
DB_AVAILABLE = False
db_session = None
engine = None
Base = None

try:
    # Intentamos importar tu configuración original
    from config import Config, get_logger, setup_logging
    from middleware import register_middleware
    
    # Intentamos conectar a la DB
    from database import db_session, engine, Base
    import models # Importar modelos para SQLAlchemy
    
    DB_AVAILABLE = True
    setup_logging()
    logger = get_logger(__name__)
    logger.info("✅ Dependencias y DB cargadas correctamente.")
except Exception as e:
    # Si falla, configuramos un logger básico y seguimos en modo "Supervivencia"
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.error(f"⚠️ ERROR CRÍTICO AL INICIAR: {e}")
    # Definimos una clase Config dummy para que no rompa más abajo
    class Config:
        ENV = os.environ.get("ENV", "production")
        DEBUG = os.environ.get("DEBUG", "False") == "True"
        ALLOWED_ORIGINS = ["*"]
        PORT = int(os.environ.get("PORT", 8080))
        def validate(self): pass

# --- 2. IMPORTACIÓN DEL SEED ---
seed_database_func = None
try:
    from seed import seed_database
    seed_database_func = seed_database
except ImportError:
    logger.warning("⚠️ No se encontró el archivo seed.py")


def create_app(config: Config | None = None) -> Flask:
    app = Flask(__name__)

    if config is None:
        config = Config()

    # Validar configuracion (Protegido)
    try:
        config.validate()
    except Exception as e:
        logger.error(f"Error config: {e}")

    app.config.from_object(config)

    # Configurar CORS
    _configure_cors(app, config.ALLOWED_ORIGINS)

    # Configurar DB (Solo si está disponible)
    if DB_AVAILABLE:
        _configure_database(app)
        # Inicializar tablas de forma segura
        with app.app_context():
            try:
                Base.metadata.create_all(bind=engine)
            except Exception as e:
                logger.error(f"❌ Error conectando a DB en arranque: {e}")

    # Registrar middleware
    if DB_AVAILABLE:
        try:
            register_middleware(app)
        except Exception:
            pass

    # Registrar blueprints
    _register_blueprints(app)

    # Rutas básicas + SEED ENDPOINT
    _register_basic_routes(app)

    return app


def _configure_cors(app: Flask, allowed_origins: list[str]) -> None:
    CORS(app, resources={r"/api/*": {"origins": allowed_origins, "supports_credentials": True}})


def _configure_database(app: Flask) -> None:
    @app.teardown_appcontext
    def shutdown_session(exception: BaseException | None = None) -> None:
        if DB_AVAILABLE and db_session:
            db_session.remove()


def _register_blueprints(app: Flask) -> None:
    if not DB_AVAILABLE:
        logger.warning("🚫 DB no disponible: No se cargarán las rutas de negocio.")
        return

    try:
        from routes import locales_bp
        from routes.auth import auth_bp
        from routes.empresa import empresa_bp
        from routes.favoritos import favoritos_bp
        from routes.invitaciones import invitaciones_bp
        from routes.opiniones import opiniones_bp
        from routes.reservas import reservas_bp

        blueprints = [
            (locales_bp, "locales"), (auth_bp, "auth"), (opiniones_bp, "opiniones"),
            (reservas_bp, "reservas"), (favoritos_bp, "favoritos"),
            (empresa_bp, "empresa"), (invitaciones_bp, "invitaciones"),
        ]

        for blueprint, name in blueprints:
            app.register_blueprint(blueprint)
            
    except ImportError as e:
        logger.error(f"Error importando rutas: {e}")


def _register_basic_routes(app: Flask) -> None:
    
    @app.route("/")
    def index():
        return health_check()

    @app.route("/health")
    @app.route("/api/health")
    def health_check():
        status = "ok" if DB_AVAILABLE else "error_db"
        return jsonify({
            "status": status,
            "message": "Backend Flask funcionando",
            "db_connected": DB_AVAILABLE
        }), 200

    # ====================================================================
    # EL ENDPOINT MÁGICO PARA GITHUB ACTIONS (AGREGADO)
    # ====================================================================
    @app.route("/debug/force-seed", methods=['POST'])
    def force_seed_endpoint():
        # Validaciones para que funcione
        if not DB_AVAILABLE:
            return jsonify({"error": "Sin conexión a DB", "message": "La app arrancó sin base de datos."}), 500
        
        if not seed_database_func:
            return jsonify({"error": "Falta seed.py"}), 500
        
        # Seguridad
        env = os.environ.get("ENV", "production")
        if env == "production":
            return jsonify({"error": "Forbidden"}), 403

        try:
            logger.info("🌱 Ejecutando Seed a pedido...")
            start_time = time.time()
            seed_database_func()
            elapsed = time.time() - start_time
            return jsonify({"status": "success", "message": f"Seed completado en {elapsed:.2f}s"})
        except Exception as e:
            logger.error(f"❌ Error en seed: {e}")
            return jsonify({"error": str(e)}), 500


# Crear instancia
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)