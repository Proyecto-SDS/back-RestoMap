"""
Punto de entrada principal - VERSION BLINDADA PARA CLOUD RUN
Ruta: src/main.py
"""
import sys
import os
import time
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configurar logging básico inicial
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. IMPORTACIONES A PRUEBA DE FALLOS ---
# En Cloud Run, si la DB falla al inicio, la app debe arrancar igual para mostrar logs.
DB_AVAILABLE = False
db_session = None
engine = None
Base = None

try:
    # Ajuste de path para que encuentre los módulos dentro de src
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)

    # Importaciones críticas
    from config import Config, get_logger, setup_logging
    from middleware import register_middleware
    from database import db_session, engine, Base
    import models 
    
    DB_AVAILABLE = True
    setup_logging()
    logger = get_logger(__name__)
    logger.info("✅ Dependencias y DB cargadas correctamente.")
except Exception as e:
    logger.error(f"⚠️ ERROR CRÍTICO DE IMPORTACIÓN (Modo Supervivencia): {e}")
    # Clase Config Dummy para que el código no rompa
    class Config:
        ENV = os.environ.get("ENV", "production")
        DEBUG = os.environ.get("DEBUG", "False") == "True"
        ALLOWED_ORIGINS = ["*"]
        PORT = int(os.environ.get("PORT", 8080))
        def validate(self): pass

# --- 2. IMPORTACIÓN DEL SEED (Adaptado a tu ruta src/db/seed.py) ---
seed_database_func = None
seed_source = "Ninguno"
try:
    # Intento 1: Ruta absoluta desde src
    from db.seed import seed_database
    seed_database_func = seed_database
    seed_source = "db.seed"
except ImportError:
    try:
        # Intento 2: Ruta si estamos dentro de src
        from seed import seed_database
        seed_database_func = seed_database
        seed_source = "seed"
    except ImportError:
        logger.warning("⚠️ No se encontró el archivo seed.py en db/seed.py ni en la raíz.")


def create_app(config: Config | None = None) -> Flask:
    app = Flask(__name__)

    if config is None:
        config = Config()

    try:
        config.validate()
    except Exception:
        pass

    app.config.from_object(config)

    # Configurar CORS
    CORS(app, resources={r"/api/*": {"origins": config.ALLOWED_ORIGINS, "supports_credentials": True}})

    # Configurar DB (Solo si está disponible)
    if DB_AVAILABLE:
        _configure_database(app)
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

    # Registrar Blueprints
    _register_blueprints(app)

    # Rutas Básicas + Endpoint de Seed
    _register_basic_routes(app)

    return app


def _configure_database(app: Flask) -> None:
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if DB_AVAILABLE and db_session:
            db_session.remove()


def _register_blueprints(app: Flask) -> None:
    if not DB_AVAILABLE:
        return

    try:
        from routes import locales_bp, auth_bp, opiniones_bp, reservas_bp, favoritos_bp
        app.register_blueprint(locales_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(opiniones_bp)
        app.register_blueprint(reservas_bp)
        app.register_blueprint(favoritos_bp)
    except Exception as e:
        logger.error(f"Error cargando rutas: {e}")


def _register_basic_routes(app: Flask) -> None:
    
    @app.route("/")
    @app.route("/health")
    def health_check():
        status = "ok" if DB_AVAILABLE else "error_db"
        return jsonify({
            "status": status,
            "message": "Backend funcionando",
            "db_connected": DB_AVAILABLE,
            "seed_source": seed_source
        }), 200

    # --- ENDPOINT PARA GITHUB ACTIONS ---
    @app.route("/debug/force-seed", methods=['POST'])
    def force_seed_endpoint():
        if not DB_AVAILABLE:
            return jsonify({"error": "Sin conexión a DB", "message": "Revisa los logs de arranque."}), 500
        
        if not seed_database_func:
            return jsonify({"error": "Falta seed.py", "message": "No se encontró src/db/seed.py"}), 500
        
        env = os.environ.get("ENV", "production")
        if env == "production":
            return jsonify({"error": "Forbidden"}), 403

        try:
            logger.info(f"🌱 Ejecutando Seed desde {seed_source}...")
            start_time = time.time()
            seed_database_func()
            elapsed = time.time() - start_time
            return jsonify({"status": "success", "message": f"Seed ok en {elapsed:.2f}s"})
        except Exception as e:
            logger.error(f"❌ Error en seed: {e}")
            return jsonify({"error": str(e)}), 500


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)