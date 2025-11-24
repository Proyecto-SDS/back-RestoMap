from db.sesion import engine
from db.base import Base
from modelos import *

print("Creando tablas...")
Base.metadata.create_all(bind=engine)
print("Listo.")