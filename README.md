# Backend — Base de datos local (Postgres)

Este README explica lo mínimo para levantar la base de datos localmente y preparar el backend para pruebas locales.

Requisitos
- Docker & Docker Compose (para Postgres) https://www.docker.com/products/docker-desktop/.
- Python 3.12.10 (crear virtualenv y usar `pip install -r requirements.txt`, dentro del repo) https://www.python.org/downloads/windows/.

Pasos rápidos

1) Copiar plantilla de variables y editar
- Copiar `.env.example` a `.env` y rellenar:
  - Al menos: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` (usados por [`db/base.py`](db/base.py)).
  - Además, para que docker-compose levante Postgres sin cambios en `docker-compose.yml`.
  - Ejemplo mínimo (.env):
    ```bash
    ENV=dev # tal cual
    DB_USER=tsdspgsql # la de tu psql
    DB_PASSWORD=contrasena # la de tu psql
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=bd_tsds # ideal dejarlo para consistencia entre todos
    ```

2) Levantar Postgres
- Desde la carpeta `app/backend`:
  ```bash
  docker compose up -d
  ```
  (usa [`docker-compose.yml`](docker-compose.yml) y el `.env` local)

3) Preparar entorno Python
- Crear/activar virtualenv e instalar paquetes:
  ```bash
  python -m venv venv
  # Bash (Linux/macOS)
  source venv/Scripts/activate o source venv/bin/activate
  # Windows
  venv\Scripts\activate o source venv/bin/activate
  # luego descargar los requerimientos
  pip install -r requirements.txt
  ```

4) Crear tablas
- Usar SQLAlchemy directo:
  ```
  # ejecutar el script en `app/backend`:
  python -m config.crear_db_sqla
  ```
  Esto usa [`config/crear_db_sqla.py`](config/crear_db_sqla.py) que carga [`modelos/__init__.py`](modelos/__init__.py) y ejecuta `Base.metadata.create_all(bind=engine)`.

  Alembic usa [`migraciones/env.py`](migraciones/env.py) y la URL montada desde las mismas variables de entorno.

---------------------------- 5 ESTA MALO! ----------------------------
5) Poblar tablas fijas
- Ejecutar la función de seed:
  ```bash
  python -c "from db.tablas_fijas import tablas_fijas; tablas_fijas()"
  ```
---------------------------- 5 ESTA MALO! ----------------------------

6) Comprobar conexión
- Conectar con `psql` o cliente a `DB_HOST:DB_PORT` con credenciales de `.env`.
- También se puede levantar el backend mínimo para comprobar conexión HTTP:
  ```bash
  # ejemplo con uvicorn si se instala (FastAPI):
  uvicorn main:app --reload --port 8000
  ```