from flask import Flask, jsonify
from flask_cors import CORS
from database import db_session, engine, Base
import os
import logging
import time

# Importamos modelos para chequeos
import models
from models import Local

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Intentar importar el script de seed de forma segura
seed_database_func = None
try:
    # Intenta importar desde reboot_db.py
    from reboot_db import seed_database
    seed_database_func = seed_database
except ImportError:
    try:
        # Intento alternativo desde seeds.py
        from seeds import seed_database
        seed_database_func = seed_database
    except ImportError:
        logger.warning("⚠️ No se encontró el archivo de seeds (reboot_db.py o seeds.py)")

def create_app():
    app = Flask(__name__)
    
    # Configurar CORS dinámico
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    
    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    app.config['JSON_SORT_KEYS'] = False

    # ====================================================================
    # LÓGICA DE AUTO-POBLADO ROBUSTA (SMART SEED)
    # ====================================================================
    with app.app_context():
        try:
            logger.info("🛠️ Verificando esquema de Base de Datos...")
            # 1. Asegurar que las tablas existan
            Base.metadata.create_all(bind=engine)
            
            # 2. Lógica de Seed
            if seed_database_func:
                try:
                    # Chequeo rápido: ¿Hay datos en la tabla Local?
                    # Si falla la consulta (ej: tabla no existía), el try captura el error
                    local_existente = db_session.query(Local).first()
                    
                    if not local_existente:
                        logger.warning("📉 Base de datos detectada VACÍA. Iniciando Seed automático...")
                        start_time = time.time()
                        
                        # --- EJECUCIÓN DEL SEED ---
                        seed_database_func()
                        # --------------------------
                        
                        elapsed = time.time() - start_time
                        logger.info(f"✅ Seed completado exitosamente en {elapsed:.2f} segundos.")
                    else:
                        logger.info("📦 La base de datos ya tiene datos. Omitiendo seed.")
                        
                except Exception as e_seed:
                    # IMPORTANTE: Capturamos el error pero NO detenemos la app
                    # Esto permite que Cloud Run marque el deploy como exitoso
                    logger.error(f"❌ ERROR EN SEED AUTOMÁTICO (La app iniciará igual): {e_seed}")
            else:
                logger.warning("⚠️ Función seed_database no cargada, saltando auto-poblado.")

        except Exception as e:
            logger.error(f"❌ Error crítico inicializando DB: {e}")
            # Continuamos para permitir ver logs en Cloud Run
    # ====================================================================
    
    # Manejo de cierre de sesión de base de datos
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    # Ruta de prueba (Health check)
    @app.route("/")
    def health_check():
        return jsonify({"status": "ok", "message": "Backend Flask funcionando correctamente"})

    # ====================================================================
    # REGISTRO DE BLUEPRINTS (RUTAS) - CORREGIDO
    # ====================================================================
    # Importamos explícitamente desde cada archivo para evitar ImportError
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
        logger.info("✅ Rutas registradas correctamente.")
        
    except ImportError as e:
        logger.error(f"❌ ERROR CRÍTICO IMPORTANDO RUTAS: {e}")
        # Si faltan rutas, la app arranca pero sin endpoints (para poder ver el log)

    return app

app = create_app()

if __name__ == "__main__":

    port = int(os.environ.get("PORT", "5000"))

    # Activar debug mode si ENV es dev o development
    env = os.environ.get("ENV", "production")
    debug_mode = env in ["dev", "development"]

    logger.info(f"Iniciando servidor en el puerto: {port}")
    logger.info(f"Modo debug: {debug_mode} (ENV={env})")
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
