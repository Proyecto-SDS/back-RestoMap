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

# Intentamos importar el seed seguro
seed_database_func = None
try:
    from seeds import seed_database
    seed_database_func = seed_database
except ImportError:
    logger.warning("⚠️ No se encontró seeds.py")

def create_app():
    app = Flask(__name__)
    
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    CORS(app, resources={r"/api/*": {"origins": allowed_origins, "supports_credentials": True}})
    app.config['JSON_SORT_KEYS'] = False

    # 1. Crear Tablas al inicio (Safe)
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
        return jsonify({"status": "ok"})

    # ====================================================================
    # ENDPOINT PARA GITHUB ACTIONS (SEED SEGURO)
    # ====================================================================
    @app.route("/debug/force-seed", methods=['POST'])
    def force_seed_endpoint():
        # 1. Candado de Seguridad para Producción
        env = os.environ.get("ENV", "production")
        if env == "production":
            return jsonify({
                "error": "Forbidden",
                "message": "🚫 El seed manual está bloqueado en entorno de Producción."
            }), 403

        if not seed_database_func:
            return jsonify({"error": "No script found"}), 500
        
        try:
            logger.info("🌱 Ejecutando Seed Seguro...")
            seed_database_func() # <--- Ya no borra nada, solo agrega si falta
            return jsonify({"status": "success", "message": "Datos verificados/agregados."})
        except Exception as e:
            logger.error(f"❌ Error seed: {e}")
            return jsonify({"error": str(e)}), 500

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