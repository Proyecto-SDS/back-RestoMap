"""
Configuración de la base de datos PostgreSQL
Gestiona la conexión, engine y sesiones de SQLAlchemy
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# Cargar variables de entorno desde .env
load_dotenv()

# Base declarativa de SQLAlchemy
# NOTA: Esta Base será importada por models.py
Base = declarative_base()

# Leer las variables de entorno para la base de datos
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Validar que todas las variables necesarias estén presentes
if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    raise ValueError("Una o más variables de entorno de la base de datos no están configuradas.")

# Construir la URL de la base de datos
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear engine de SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# Crear SessionLocal (factory de sesiones)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# Crear sesión global con scoped_session (thread-safe)
db_session = scoped_session(SessionLocal)

# Función helper para obtener sesiones en otros contextos
def get_db():
    """
    Generador de sesiones para usar en dependencias o contextos.
    Uso:
        db = next(get_db())
        try:
            # usar db
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Exponer elementos para importación desde otros módulos
__all__ = ["Base", "engine", "DATABASE_URL", "db_session", "SessionLocal", "get_db"]
