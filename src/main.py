from flask import Flask, jsonify, request # <--- Agregamos request
from flask_cors import CORS
from database import db_session, engine, Base
import os
import logging

import models 

# --- IMPORTACIÓN DEL SCRIPT DE SEEDS ---
# Asumiendo que guardaste el script anterior como 'reboot_db.py'
# Si lo guardaste como 'seeds.py', cambia a: from seeds import seed_database
try:
    from reboot_db import seed_database
except ImportError:
    # Si no encuentra el archivo, definimos una función dummy para que no rompa el servidor
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ No se encontró el archivo 'reboot_db.py'. El endpoint de reset fallará.")
    def seed_database():
        raise Exception("El archivo reboot_db.py no existe o no se pudo importar.")

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

    # Esto revisa si las tablas existen en GCP. Si no, las crea.
    with app.app_context():
        try:
            logger.info("Verificando existencia de tablas en la BD...")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Tablas verificadas/creadas correctamente.")
        except Exception as e:
            logger.error(f"❌ Error al crear tablas: {e}")
    
    # Manejo de cierre de sesión de base de datos
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    # Ruta de prueba (Health check)
    @app.route("/")
    def health_check():
        return jsonify({"status": "ok", "message": "Backend Flask funcionando correctamente"})

    # ==================================================================
    # ENDPOINT DE RESETEO TOTAL (Seed)
    # ==================================================================
    @app.route("/semilla/reset-total", methods=['POST', 'GET'])
    def reset_db_endpoint():
        # 1. SEGURIDAD: Verificar entorno y clave
        env = os.environ.get("ENV", "production")
        secret_key = request.args.get("key") # Se espera ?key=soyeljefe en la URL
        
        # Si es producción, OBLIGAMOS a tener la clave secreta
        if env == "production" and secret_key != "soyeljefe":
            return jsonify({
                "error": "⛔ ACCESO DENEGADO",
                "message": "No puedes resetear la base de datos de producción sin la clave maestra."
            }), 403

        try:
            logger.warning(f"☢️ INICIANDO RESET DE BASE DE DATOS (Entorno: {env})")
            
            # Ejecutamos la función importada del script de seeds
            seed_database()
            
            return jsonify({
                "status": "success",
                "message": "✅ Base de datos reiniciada y poblada exitosamente.",
                "env": env
            })
        except Exception as e:
            logger.error(f"❌ Error fatal en reset: {str(e)}")
            return jsonify({"error": str(e)}), 500
    # ==================================================================

    # Registrar Blueprints (Rutas)
    from routes import locales_bp
    from routes.auth import auth_bp
    from routes.opiniones import opiniones_bp
    from routes.reservas import reservas_bp
    from routes.favoritos import favoritos_bp
    
    app.register_blueprint(locales_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(opiniones_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(favoritos_bp)

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
    logger.info(f"Iniciando servidor en el puerto: {port}")
    logger.info(f"Modo debug: {debug_mode} (ENV={env})")
    # Ejecutar en modo debug si se corre directamente
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
