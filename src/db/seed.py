"""
Script de Seed (Datos Iniciales)
Puebla la base de datos con datos de referencia y ejemplos de testing
Version optimizada para Cloud Run y Docker
"""

import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv

# --- 1. CONFIGURACION DE RUTAS (CRUCIAL PARA CLOUD RUN Y DOCKER) ---
# Obtenemos la ruta absoluta de este archivo (src/db/seed.py)
current_dir = Path(__file__).resolve().parent
# Obtenemos la ruta 'src' (padre de db)
src_dir = current_dir.parent
# Agregamos 'src' al path de Python si no esta
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

# Configurar logging usando el sistema centralizado
from config import get_logger, setup_logging  # noqa: E402

setup_logging()
logger = get_logger(__name__)

try:
    # --- 2. IMPORTACIONES ---
    # Importamos la fabrica de sesiones desde database.py
    from database import Base, SessionLocal, engine

    # Importamos las funciones de seed
    # Intentamos importar desde 'seeds' (si corremos en src/db) o 'db.seeds' (si corremos en src)
    try:
        # pyrefly: ignore [missing-import]
        from seeds import (
            create_catalogs,
            create_interactions,
            create_locals,
            create_orders,
            create_products,
            create_qrs,
            create_reservations,
            create_roles,
            create_users,
        )
    except ImportError:
        from db.seeds import (
            create_catalogs,
            create_interactions,
            create_locals,
            create_orders,
            create_products,
            create_qrs,
            create_reservations,
            create_roles,
            create_users,
        )

except ImportError as e:
    logger.error(f"Error critico de importacion: {e}")
    logger.error(
        "Asegúrate de que estas ejecutando esto con PYTHONPATH=/app/src o desde la raiz correcta."
    )
    sys.exit(1)


def seed_database():
    """Pobla la base de datos con datos iniciales"""

    # --- LIMPIEZA DE BASE DE DATOS ---
    logger.info("♻Limpiando base de datos completa...")
    try:
        # Para PostgreSQL, usar DROP SCHEMA CASCADE es más confiable
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            conn.commit()

        # Ahora crear todas las tablas desde cero
        Base.metadata.create_all(bind=engine)
        logger.info("   ✓ Base de datos limpiada y recreada.")
    except Exception as e:
        logger.error(f"   Error al limpiar base de datos: {e}")
        # Si falla, intentar con el método tradicional
        try:
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            logger.info("   ✓ Base de datos limpiada (método alternativo).")
        except Exception as e2:
            logger.error(f"   Error en limpieza alternativa: {e2}")

    db = SessionLocal()
    logger.info("Iniciando proceso de Seed en la base de datos...")

    try:
        create_roles(db)
        create_catalogs(db)
        create_locals(db)  # Locales primero
        create_users(db)  # Usuarios después (algunos tienen id_local)
        create_products(db)
        create_interactions(db)
        create_reservations(db)
        create_orders(db)
        create_qrs(db)

        logger.info("Base de datos poblada exitosamente con datos completos!")

    except Exception as e:
        logger.error(f"Error fatal al poblar la base de datos: {e}")
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
