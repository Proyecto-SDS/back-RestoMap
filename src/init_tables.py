import logging
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))

try:
    from database import Base, engine

    # Importamos los modelos
    from models import *  # noqa: F403 - Necesario para que SQLAlchemy detecte todos los modelos

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
