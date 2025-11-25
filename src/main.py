from flask import Flask, jsonify
from flask_cors import CORS
from database import db_session
import os

def create_app():
    app = Flask(__name__)
    
    # Configurar CORS (permitir peticiones del frontend)
    CORS(app)
    
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
    
    app.register_blueprint(locales_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(opiniones_bp)
    app.register_blueprint(reservas_bp)


    return app

app = create_app()

if __name__ == "__main__":

    port = int(os.environ.get("PORT", "5000"))

    debug_mode = os.environ.get("FLASK_ENV") == "development"

    print(f"Iniciando servidor en el puerto: {port}")
    # Ejecutar en modo debug si se corre directamente
    app.run(host="0.0.0.0", port=port, debug=debug_mode)