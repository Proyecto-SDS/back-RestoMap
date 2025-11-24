from sqlalchemy.orm import sessionmaker, scoped_session
from .base import engine

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

db_session = scoped_session(SessionLocal)

def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()
        db_session.remove()

__all__ = ("engine", "SessionLocal", "db_session", "get_db")