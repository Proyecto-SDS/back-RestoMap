from flask import Flask, jsonify, request
from flask_cors import CORS
from database import db_session, engine, Base
import os
import logging
import time

# Importamos modelos
import models

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- IMPORTACIÓN ROBUSTA DEL SCRIPT DE SEED ---
seed_database_func = None
seed_source = "Ninguno"

try:
    # 1. Intento principal: Tu ruta específica (src/db/seed.py)
    # En Python, las carpetas se navegan con puntos
    from src.db.seed import seed_database
    seed_database_func = seed_database
    seed_source = "src/db/seed.py"
except ImportError:
    try:
        # 2. Intento secundario: Si main.py ya está dentro de src
        from db.seed import seed_database
        seed_database_func = seed_database
        seed_source = "db/seed.py"
    except ImportError:
        try:
            # 3. Intento raíz: Si decidiste moverlo a la raíz
            from seed import seed_database
            seed_database_func = seed_database
            seed_source = "seed.py"
        except ImportError:
            logger.warning("⚠️ CRÍTICO: No se encontró seed_database en src/db/seed.py ni rutas alternas.")

def create_app():
    app = Flask(__name__)
    
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    CORS(app, resources={r"/api/*": {"origins": allowed_origins, "supports_credentials": True}})
    app.config['JSON_SORT_KEYS'] = False

    # 1. Crear Tablas (Schema)
    with app.app_context():
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            logger.error(f"❌ Error DB Init: {e}")

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    @app.route("/")
    def health_check():
        return jsonify({
            "status": "ok", 
            "message": "Backend funcionando",
            "seed_source": seed_source  # Te dirá qué archivo encontró
        })

    # ====================================================================
    # ENDPOINT PARA GITHUB ACTIONS
    # ====================================================================
    @app.route("/debug/force-seed", methods=['POST'])
    def force_seed_endpoint():
        if not seed_database_func:
            return jsonify({
                "error": "Script no encontrado", 
                "message": f"Se buscó en src/db/seed.py y falló. Fuente: {seed_source}"
            }), 500
        
        env = os.environ.get("ENV", "production")
        if env == "production":
            return jsonify({"error": "Forbidden", "message": "Seed bloqueado en producción"}), 403

        try:
            logger.info(f"🌱 Ejecutando Seed desde {seed_source}...")
            start_time = time.time()
            
            # Ejecutar lógica
            seed_database_func()
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Seed completado en {elapsed:.2f}s")
            return jsonify({"status": "success", "message": "Base de datos poblada correctamente"})
            
        except Exception as e:
            logger.error(f"❌ Error en seed: {e}")
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
    except ImportError:
        pass

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)