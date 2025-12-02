from flask import Flask, jsonify, request
from flask_cors import CORS
from database import db_session, engine, Base
import os
import logging
import time

# Importamos modelos para asegurar que SQLAlchemy los reconozca al crear tablas
import models
from models import Local

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- IMPORTACIÓN SEGURA DEL SCRIPT DE SEED ---
# Buscamos la función seed_database en el archivo seed.py
seed_database_func = None
try:
    from seed import seed_database
    seed_database_func = seed_database
except ImportError:
    logger.warning("⚠️ No se encontró el archivo 'seed.py'. El endpoint de seed fallará.")

def create_app():
    app = Flask(__name__)
    
    # Configurar CORS
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    CORS(app, resources={r"/api/*": {"origins": allowed_origins, "supports_credentials": True}})
    
    app.config['JSON_SORT_KEYS'] = False

    # 1. Crear Tablas al inicio (Siempre necesario)
    with app.app_context():
        try:
            logger.info("🛠️ Verificando esquema de Base de Datos...")
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            logger.error(f"❌ Error crítico inicializando DB: {e}")

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    @app.route("/")
    def health_check():
        return jsonify({"status": "ok", "message": "Backend funcionando"})

    # ====================================================================
    # ENDPOINT PARA GITHUB ACTIONS (AQUÍ ESTÁ LA MAGIA)
    # ====================================================================
    @app.route("/debug/force-seed", methods=['POST'])
    def force_seed_endpoint():
        # 1. Verificamos si logramos importar el script
        if not seed_database_func:
            return jsonify({
                "error": "Script no encontrado", 
                "message": "No existe el archivo seed.py en el servidor."
            }), 500
        
        # 2. Candado de Seguridad para Producción
        # Si ENV es production, bloqueamos el seed para no ensuciar datos reales
        env = os.environ.get("ENV", "production")
        if env == "production":
            return jsonify({
                "error": "Forbidden",
                "message": "🚫 El seed está bloqueado en Producción."
            }), 403

        try:
            logger.info("🌱 Ejecutando Seed a petición externa...")
            start_time = time.time()
            
            # Ejecutamos el seed (Seguro)
            seed_database_func()
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Seed completado en {elapsed:.2f}s")
            return jsonify({"status": "success", "message": "Base de datos poblada correctamente"})
            
        except Exception as e:
            logger.error(f"❌ Error en seed: {e}")
            # Devolvemos el error para que GitHub lo vea
            return jsonify({"error": str(e)}), 500
    # ====================================================================

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