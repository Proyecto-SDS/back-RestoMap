import sys
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- CORRECCIoN DE RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.dirname(current_dir))
# ---------------------------

try:
    from database import engine, Base
    # Importamos los modelos
    from models import * # --- AQUi ESTABA EL ERROR (Debe haber un salto de linea) ---
    def init_db():
        logger.info(f"Iniciando creacion de tablas en: {engine.url}")
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("¡Tablas creadas exitosamente!")
        except Exception as e:
            logger.error(f"Error fatal creando tablas: {e}")
            sys.exit(1)

    if __name__ == "__main__":
        init_db()

except ImportError as e:
    logger.error(f"Error de importacion (Rutas): {e}")
    sys.exit(1)