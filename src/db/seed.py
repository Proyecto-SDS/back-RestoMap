"""
Script de Seed (Datos Iniciales)
Puebla la base de datos con datos de referencia y ejemplos de testing
Version optimizada para Cloud Run y Docker
"""
import sys
import os
import logging
from dotenv import load_dotenv

# --- 1. CONFIGURACIoN DE RUTAS (CRUCIAL PARA CLOUD RUN) ---
# Obtenemos la ruta absoluta de este archivo (src/db/seed.py)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Obtenemos la ruta 'src' (padre de db)
src_dir = os.path.dirname(current_dir)
# Agregamos 'src' al path de Python si no esta
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Configuracion de Logging (para que se vea bien en Google Cloud)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # --- 2. IMPORTACIONES ---
    # Importamos la fabrica de sesiones desde database.py
    from database import SessionLocal, engine, Base
    
    # Importamos las funciones de seed
    # Intentamos importar desde 'seeds' (si corremos en src/db) o 'db.seeds' (si corremos en src)
    try:
        # pyrefly: ignore [missing-import]
        from seeds import (
            create_roles, create_catalogs, create_users, create_locals,
            create_products, create_interactions, create_reservations,
            create_orders, create_qrs
        )
    except ImportError:
        from db.seeds import (
            create_roles, create_catalogs, create_users, create_locals,
            create_products, create_interactions, create_reservations,
            create_orders, create_qrs
        )

except ImportError as e:
    logger.error(f"Error critico de importacion: {e}")
    logger.error("Asegúrate de que estas ejecutando esto con PYTHONPATH=/app/src o desde la raiz correcta.")
    sys.exit(1)

def seed_database():
    """Pobla la base de datos con datos iniciales"""
    
    # --- LIMPIEZA DE BASE DE DATOS ---
    logger.info("♻Limpiando base de datos completa...")
    try:
        # Eliminar todas las tablas y volver a crearlas
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("   ✓ Base de datos limpiada y recreada.")
    except Exception as e:
        logger.error(f"   Error al limpiar base de datos: {e}")
        # Intentamos continuar
    
    db = SessionLocal()
    logger.info("Iniciando proceso de Seed en la base de datos...")
    
    try:
        create_roles(db)
        create_catalogs(db)
        create_users(db)
        create_locals(db)
        create_products(db)
        create_interactions(db)
        create_reservations(db)
        create_orders(db)
        create_qrs(db)
        
        logger.info("Base de datos poblada exitosamente con datos completos!")
        
    except Exception as e:
        logger.error(f"Error fatal al poblar la base de datos: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    # Cargar variables de entorno (solo si se corre local)
    load_dotenv()
    
    # Ejecutar seed
    seed_database()
