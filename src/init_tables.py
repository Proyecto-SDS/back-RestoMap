import sys
import os

# --- CORRECCIÓN DE RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.dirname(current_dir))
# ---------------------------

try:
    from database import engine, Base
    # Asegúrate de importar tus modelos aquí
    # Si tus modelos están en models.py, esto está bien:
    from models import * def init_db():
        print(f"Iniciando creación de tablas en: {engine.url}")
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ ¡Tablas creadas exitosamente!")
        except Exception as e:
            print(f"❌ Error fatal creando tablas: {e}")
            sys.exit(1)

    if __name__ == "__main__":
        init_db()

except ImportError as e:
    print(f"❌ Error de importación (Rutas): {e}")
    sys.exit(1)