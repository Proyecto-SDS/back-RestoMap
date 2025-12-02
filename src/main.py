from flask import Flask, jsonify
from flask_cors import CORS
from database import db_session
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Configurar CORS dinámico
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
    
    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Configuración básica
    app.config['JSON_SORT_KEYS'] = False
    
    # Manejo de cierre de sesión de base de datos
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    # Ruta de prueba (Health check)
    @app.route("/")
    def health_check():
        return jsonify({"status": "ok", "message": "Backend Flask funcionando correctamente"})

    # Registrar Blueprints (Rutas)
    from routes import locales_bp
    from routes.auth import auth_bp
    from routes.opiniones import opiniones_bp
    from routes.reservas import reservas_bp
    from routes.favoritos import favoritos_bp
    from routes.gestionlocal import gestionlocal_bp
    from dashboard_mesero.routes import pedidos_bp
    
    app.register_blueprint(locales_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(opiniones_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(favoritos_bp)
    app.register_blueprint(gestionlocal_bp)

    app.register_blueprint(pedidos_bp)

    return app

app = create_app()

if __name__ == "__main__":

    port = int(os.environ.get("PORT", "5000"))

    # Activar debug mode si ENV es dev o development
    env = os.environ.get("ENV", "production")
    debug_mode = env in ["dev", "development"]

    logger.info(f"Iniciando servidor en el puerto: {port}")
    logger.info(f"Modo debug: {debug_mode} (ENV={env})")
    # Ejecutar en modo debug si se corre directamente
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
