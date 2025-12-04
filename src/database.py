"""
Configuracion de la base de datos PostgreSQL
Gestiona la conexion, engine y sesiones de SQLAlchemy
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

# Cargar variables de entorno desde .env (solo para local)
load_dotenv()

# Base declarativa de SQLAlchemy
Base = declarative_base()

# Leer las variables de entorno
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
# Usamos '5432' por defecto si no existe la variable, para evitar errores en Cloud Run
DB_PORT = os.getenv("DB_PORT", "5432")

# Validar solo las variables CRiTICAS (Quitamos DB_PORT de la validacion obligatoria)
if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    raise ValueError(
        "Faltan variables de entorno criticas (DB_USER, DB_PASSWORD, DB_HOST o DB_NAME)."
    )

# pyrefly: ignore [missing-attribute]
if DB_HOST.startswith("/cloudsql"):
    # Conexion via Unix Socket (Para Cloud Run)
    # Formato: postgresql://user:pass@/dbname?host=/cloudsql/instance
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?host={DB_HOST}"
else:
    # Conexion via TCP (Para Local)
    # Formato: postgresql://user:pass@host:port/dbname
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear engine de SQLAlchemy
# pool_pre_ping=True es vital para evitar desconexiones en la nube
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# Crear SessionLocal (factory de sesiones)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# Crear sesion global con scoped_session (thread-safe)
db_session = scoped_session(SessionLocal)


# Funcion helper para obtener sesiones en otros contextos
def get_db():
    """
    Generador de sesiones para usar en dependencias o contextos.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Exponer elementos
__all__ = ["DATABASE_URL", "Base", "SessionLocal", "db_session", "engine", "get_db"]
