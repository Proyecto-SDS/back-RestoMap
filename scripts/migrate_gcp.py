#!/usr/bin/env python3
"""
Script de migracion para Google Cloud Platform (Cloud Run)
Ejecuta las migraciones de Alembic de forma segura en produccion
"""

import os
import sys
from pathlib import Path

# Agregar src al path para imports
src_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_dir))

# Configurar logging usando el sistema centralizado
from config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def validate_environment():
    """Valida que las variables de entorno necesarias estén presentes"""
    required_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
        return False

    logger.info("✓ Variables de entorno validadas")
    return True


def check_database_connection():
    """Verifica la conexión a la base de datos antes de migrar"""
    try:
        from sqlalchemy import create_engine, text

        from database import DATABASE_URL

        logger.info("Verificando conexión a la base de datos...")
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

        logger.info("✓ Conexión a la base de datos exitosa")
        return True

    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return False


def run_migrations():
    """Ejecuta las migraciones de Alembic"""
    try:
        from alembic.config import Config

        from alembic import command

        logger.info("Iniciando proceso de migración...")

        # Configurar Alembic
        alembic_cfg = Config("alembic.ini")

        # Obtener la revisión actual
        logger.info("Revisión actual de la base de datos:")
        command.current(alembic_cfg, verbose=True)

        # Ejecutar migraciones
        logger.info("Ejecutando migraciones a HEAD...")
        command.upgrade(alembic_cfg, "head")

        # Mostrar estado final
        logger.info("Migraciones completadas. Estado final:")
        command.current(alembic_cfg, verbose=True)

        logger.info("✓ Migraciones aplicadas exitosamente")
        return True

    except Exception as e:
        logger.error(f"Error ejecutando migraciones: {e}")
        import traceback

        traceback.print_exc()
        return False


def check_if_database_is_empty():
    """Verifica si la base de datos está vacía (primera vez)"""
    try:
        from sqlalchemy import create_engine, inspect

        from database import DATABASE_URL

        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Si no hay tablas o solo está alembic_version, consideramos que está vacía
        is_empty = len(tables) == 0 or (
            len(tables) == 1 and "alembic_version" in tables
        )

        if is_empty:
            logger.info("Base de datos vacía detectada - se ejecutarán seeds")
        else:
            logger.info(f"Base de datos contiene {len(tables)} tablas")

        return is_empty

    except Exception as e:
        logger.warning(f"No se pudo verificar estado de BD: {e}")
        return False


def run_seeds():
    """Ejecuta los seeds de datos iniciales"""
    try:
        logger.info("Ejecutando seeds de datos iniciales...")

        # Importar y ejecutar el script de seed
        import subprocess

        result = subprocess.run(
            ["python", "src/db/seed.py"],
            capture_output=True,
            text=True,
            check=True,
        )

        logger.info(result.stdout)
        logger.info("✓ Seeds ejecutados exitosamente")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Error ejecutando seeds: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado ejecutando seeds: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("SCRIPT DE MIGRACIÓN PARA GCP CLOUD RUN")
    logger.info("=" * 60)

    # Paso 1: Validar entorno
    if not validate_environment():
        logger.error("Falló la validación del entorno")
        sys.exit(1)

    # Paso 2: Verificar conexión
    if not check_database_connection():
        logger.error("Falló la conexión a la base de datos")
        sys.exit(1)

    # Paso 3: Verificar si es primera vez (BD vacía)
    is_first_time = check_if_database_is_empty()

    # Paso 4: Ejecutar migraciones
    if not run_migrations():
        logger.error("Falló la ejecución de migraciones")
        sys.exit(1)

    # Paso 5: Ejecutar seeds solo si es primera vez
    if is_first_time:
        logger.info("Primera inicialización detectada - ejecutando seeds...")
        if not run_seeds():
            logger.warning("Los seeds fallaron, pero las migraciones están OK")
            logger.warning("Puedes ejecutar seeds manualmente si es necesario")
    else:
        logger.info("Base de datos ya inicializada - omitiendo seeds")

    logger.info("=" * 60)
    logger.info("MIGRACIÓN COMPLETADA CON ÉXITO")
    logger.info("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
