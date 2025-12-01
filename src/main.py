from flask import Flask, jsonify
from flask_cors import CORS
from database import db_session, engine, Base
import os
import logging
import time
import threading # <--- 1. IMPORTAR THREADING

# Importamos modelos
import models
from models import Local

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Intentar importar el script de seed
seed_database_func = None
try:
    from reboot_db import seed_database
    seed_database_func = seed_database
except ImportError:
    try:
        from seeds import seed_database
        seed_database_func = seed_database
    except ImportError:
        logger.warning("⚠️ No se encontró el archivo de seeds.")

def create_app():
    app = Flask(__name__)
    
    # Configurar CORS
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    CORS(app, resources={r"/api/*": {"origins": allowed_origins, "supports_credentials": True}})
    
    app.config['JSON_SORT_KEYS'] = False

    # ====================================================================
    # LÓGICA DE AUTO-POBLADO EN SEGUNDO PLANO (THREADING)
    # ====================================================================
    with app.app_context():
        try:
            logger.info("🛠️ Verificando esquema de Base de Datos...")
            Base.metadata.create_all(bind=engine)
            
            if seed_database_func:
                try:
                    # Verificación rápida (Síncrona)
                    local_existente = db_session.query(Local).first()
                    
                    if not local_existente:
                        logger.warning("📉 DB Vacía. Iniciando Seed en SEGUNDO PLANO...")
                        
                        # --- FUNCIÓN WRAPPER PARA EL HILO ---
                        def run_seed_in_background(app_context):
                            # Necesitamos empujar el contexto de la app dentro del hilo
                            with app_context:
                                try:
                                    logger.info("🧵 Hilo de Seed iniciado...")
                                    start_time = time.time()
                                    seed_database_func()
                                    elapsed = time.time() - start_time
                                    logger.info(f"✅ Hilo de Seed completado en {elapsed:.2f}s")
                                except Exception as e:
                                    logger.error(f"❌ Error en Hilo de Seed: {e}")
                        
                        # --- LANZAR EL HILO ---
                        # Esto permite que Flask continúe cargando INMEDIATAMENTE
                        # mientras la base de datos se llena en paralelo.
                        seed_thread = threading.Thread(target=run_seed_in_background, args=(app.app_context(),))
                        seed_thread.start()
                        
                    else:
                        logger.info("📦 La base de datos ya tiene datos.")
                        
                except Exception as e_seed:
                    logger.error(f"❌ Error al intentar iniciar seed: {e_seed}")
            
        except Exception as e:
            logger.error(f"❌ Error crítico inicializando DB: {e}")
    # ====================================================================

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    @app.route("/")
    def health_check():
        return jsonify({"status": "ok", "message": "Backend funcionando"})

    # Registro de Rutas
    try:
        from routes.locales import locales_bp
        from routes.auth import auth_bp
        from routes.opiniones import opiniones_bp
        from routes.reservas import reservas_bp
        from routes.favoritos import favoritos_bp
        
        app.register_blueprint(locales_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(opiniones_bp)
        app.register_blueprint(reservas_bp)
        app.register_blueprint(favoritos_bp)
        
    except ImportError as e:
        logger.error(f"❌ ERROR IMPORTANDO RUTAS: {e}")

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug_mode = os.environ.get("ENV") in ["dev", "development"]
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
