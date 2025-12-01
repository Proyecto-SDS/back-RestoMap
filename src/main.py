from flask import Flask, jsonify
from flask_cors import CORS
from database import db_session, engine, Base
import os
import logging

# Importamos los modelos para poder verificar si existen datos
import models
from models import Local 

# Importamos el script de seed
# Asegúrate de que el archivo se llame 'reboot_db.py' o 'seeds.py'
try:
    from reboot_db import seed_database
except ImportError:
    # Intento alternativo por si tienes el archivo con otro nombre
    try:
        from seeds import seed_database
    except ImportError:
        seed_database = None

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Configurar CORS
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "supports_credentials": True
        }
    })
    
    app.config['JSON_SORT_KEYS'] = False

    # ====================================================================
    # LÓGICA DE AUTO-POBLADO (SMART SEED)
    # ====================================================================
    with app.app_context():
        try:
            logger.info("🛠️ Verificando esquema de Base de Datos...")
            # 1. Asegurar que las tablas existan (Create if not exists)
            Base.metadata.create_all(bind=engine)
            
            # 2. Verificar si hay datos
            # Usamos la tabla 'Local' como referencia. Si no hay locales, asumimos que está vacía.
            if seed_database:
                try:
                    # Buscamos si existe al menos un local
                    local_existente = db_session.query(Local).first()
                    
                    if not local_existente:
                        logger.warning("📉 Base de datos detectada VACÍA. Ejecutando Seed automático...")
                        
                        # Ejecutamos el poblado
                        seed_database()
                        
                        logger.info("✅ Seed completado exitosamente.")
                    else:
                        logger.info("📦 La base de datos ya tiene datos. Saltando Seed.")
                except Exception as e:
                    logger.error(f"❌ Error durante el chequeo/seed automático: {e}")
            else:
                logger.warning("⚠️ No se encontró la función seed_database, saltando auto-poblado.")

        except Exception as e:
            logger.error(f"❌ Error crítico inicializando DB: {e}")
    # ====================================================================

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    @app.route("/")
    def health_check():
        return jsonify({"status": "ok", "message": "Backend funcionando correctamente"})

    # Registrar Blueprints
    from routes import locales_bp, auth_bp, opiniones_bp, reservas_bp, favoritos_bp
    
    app.register_blueprint(locales_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(opiniones_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(favoritos_bp)

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    # En local activamos debug, en nube no
    debug_mode = os.environ.get("ENV") in ["dev", "development"]
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
