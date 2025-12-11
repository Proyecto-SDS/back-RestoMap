# Backend - Sistema de Gestión de Locales

Sistema backend basado en Flask + SQLAlchemy + PostgreSQL para gestión de locales, pedidos y reservas.

## Inicio Rápido (Desarrollo Local)

```bash
# 1. Clonar el repositorio
git clone https://github.com/Proyecto-SDS/back-RestoMap.git
cd back-RestoMap

# 2. Ejecutar script de configuración
./scripts/setup_local.sh  # Linux/macOS
# .\scripts\setup_local.ps1  # Windows

# 3. Editar .env con tus credenciales de PostgreSQL

# 4. Asegurarse de que PostgreSQL esté corriendo

# 5. Crear la base de datos
sudo -u postgres psql
CREATE USER myuser WITH PASSWORD 'mypassword';
CREATE DATABASE mydb OWNER myuser;
GRANT ALL PRIVILEGES ON DATABASE mydb TO myuser;
\q

# 6. Activar entorno virtual e inicializar base de datos
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows
./scripts/init_db.sh

# 7. Ejecutar backend
python src/main.py
```

La API estará disponible en `http://localhost:5000`

## Tabla de Contenido

- [Inicio Rápido](#inicio-rápido-desarrollo-local)
- [Requisitos](#requisitos)
- [Configuración](#configuración)
- [Desarrollo Local (Sin Docker)](#desarrollo-local-sin-docker)
- [Uso con Docker (Opcional)](#uso-con-docker-opcional)
- [Migraciones de Base de Datos](#migraciones-de-base-de-datos)
- [API Endpoints](#api-endpoints)

## Requisitos

### Desarrollo Local (Recomendado)

- Python 3.12 o superior
- PostgreSQL 14 o superior
- pip (gestor de paquetes de Python)

### Desarrollo con Docker (Opcional)

- Docker Desktop
- Docker Compose

## Configuración

### Variables de Entorno

Copia el archivo `.env.example` a `.env`:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
# Base de Datos (Configuración Local)
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_HOST=localhost       # localhost para desarrollo local, 'db' si usas Docker
DB_PORT=5432
DB_NAME=tu_bd

# PostgreSQL (Solo para Docker - Opcional)
POSTGRES_USER=tu_usuario
POSTGRES_PASSWORD=tu_contraseña
POSTGRES_DB=tu_bd

# Configuración General
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001 # Lista separada por comas
ENV=development # 'production' o 'development'
JWT_SECRET_KEY=dev-secret-key-change-in-production-2025
```

## Desarrollo Local (Sin Docker)

Esta es la forma **recomendada** de trabajar con el proyecto durante el desarrollo.

### Paso 1: Instalar PostgreSQL

Instala PostgreSQL en tu sistema:

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**macOS (con Homebrew):**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Windows:**
Descarga e instala desde [postgresql.org](https://www.postgresql.org/download/windows/)

### Paso 2: Crear la Base de Datos

```bash
# Conectarse a PostgreSQL como superusuario
sudo -u postgres psql

# Crear usuario y base de datos
CREATE USER tu_usuario WITH PASSWORD 'tu_contraseña';
CREATE DATABASE tu_bd OWNER tu_usuario;
GRANT ALL PRIVILEGES ON DATABASE tu_bd TO tu_usuario;
\q
```

### Paso 3: Configurar Variables de Entorno

Copia y edita el archivo `.env`:

```bash
cp .env.example .env
```

Asegúrate de que `DB_HOST=localhost` en tu archivo `.env`.

### Paso 4: Crear Entorno Virtual de Python

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En Linux/macOS:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### Paso 5: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 6: Inicializar la Base de Datos

```bash
# Opción 1: Usando el script de inicialización
chmod +x scripts/init_db.sh
./scripts/init_db.sh

# Opción 2: Manualmente
python src/init_tables.py
python src/db/seed.py
```

### Paso 7: Ejecutar el Backend

```bash
# Asegúrate de que el entorno virtual esté activado
python src/main.py
```

El servidor estará disponible en `http://localhost:5000`

### Paso 8: Verificar que Funcione

En otra terminal:

```bash
# Health check
curl http://localhost:5000/

# Ver locales
curl http://localhost:5000/locales/
```

### Uso Diario (Desarrollo Local)

```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Ejecutar backend
python src/main.py

# Para detener: Ctrl+C
```

### Migraciones con Alembic (Desarrollo Local)

```bash
# Activar entorno virtual primero
source venv/bin/activate

# Generar migración
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migración
alembic upgrade head

# Ver historial
alembic history

# Ver migración actual
alembic current

# Revertir migración
alembic downgrade -1
```

## Uso con Docker (Opcional)

**Nota:** Docker es opcional. Se recomienda usar el desarrollo local para mayor simplicidad.

## Producción con Docker

El proyecto incluye un `Dockerfile` optimizado para producción que utiliza **Gunicorn** como servidor WSGI.

### Construir la imagen

```bash
docker build -t backend-restomap .
```

### Correr el contenedor

```bash
docker run -p 5000:5000 \
  -e ALLOWED_ORIGINS=https://tu-frontend.run.app \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  backend-restomap
```

> **Nota:** En producción (GCP), no uses `docker-compose` para el despliegue del backend. Usa esta imagen individual conectada a una instancia de Cloud SQL.

### Uso con Docker Compose (Desarrollo Opcional)

### Uso con Docker Compose (Desarrollo Opcional)

**Importante:** Si prefieres usar Docker, sigue estas instrucciones. De lo contrario, usa el [desarrollo local](#desarrollo-local-sin-docker).

#### Primera Vez - Paso a Paso

#### Paso 1: Configurar Variables de Entorno

Asegúrate de tener tu archivo `.env` configurado (ver sección [Configuración](#configuración)).

#### Paso 2: Construir Imágenes Docker

```bash
# Construir las imágenes de Docker (primera vez)
docker-compose build
```

**Qué hace:** Crea la imagen de Python con todas las dependencias del `requirements.txt`.

#### Paso 3: Levantar PostgreSQL

```bash
# Iniciar solo la base de datos en segundo plano
docker-compose up db -d
```

**Qué hace:** Levanta PostgreSQL en el puerto 5432.

#### Paso 4: Verificar que PostgreSQL esté listo

```bash
# Ver el estado de los contenedores
docker-compose ps
```

**Resultado esperado:**

```
NAME                  STATUS
backend-db-1          Up (healthy)
```

Espera hasta que veas `(healthy)` - esto significa que el healthcheck pasó.

#### Paso 5: Inicializar la Base de Datos

```bash
# Crear tablas con Alembic y poblar datos iniciales
docker-compose --profile init run --rm init-db
```

**Qué hace:**

1. Genera migración inicial de Alembic
2. Crea todas las tablas en PostgreSQL
3. Ejecuta `seed.py` para insertar datos de referencia (roles, comunas, etc.)
4. Inserta 5 locales de ejemplo

**Salida esperada:**

```
Iniciando configuración de base de datos...
Generando migración inicial...
Aplicando migraciones de base de datos...
Poblando datos iniciales...
  → Insertando Roles...
    ✓ Roles insertados
  → Insertando Tipos de Local...
    ✓ Tipos de Local insertados
  ...
Base de datos poblada exitosamente!
Base de datos inicializada correctamente!
```

#### Paso 6: Levantar el Backend

```bash
# Iniciar el servidor Flask
docker-compose up backend
```

**Qué hace:** Inicia la API REST de Flask en `http://localhost:5000`.

**Salida esperada:**

```
backend-backend-1  |  * Running on http://0.0.0.0:5000
backend-backend-1  |  * Debug mode: on
```

#### Paso 7: Verificar que Todo Funcione

En otra terminal o navegador:

```bash
# Health check
curl http://localhost:5000/

# Ver locales
curl http://localhost:5000/locales/
```

**Resultado esperado:**

- Health check: `{"status":"ok","message":"Backend Flask funcionando correctamente"}`
- Locales: Array JSON con 5 locales

---

### Resumen de Comandos (Primera Vez)

```bash
# Ejecutar todo de una vez (después de configurar .env)
docker-compose build
docker-compose up db -d
# Esperar ~5 segundos
docker-compose --profile init run --rm init-db
docker-compose up backend
```

---

### Uso Diario

Una vez que ya inicializaste todo, solo necesitas:

```bash
# Levantar todo (db + backend)
docker-compose up

# O en segundo plano
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f backend

# Detener todo
docker-compose down
```

---

### Reset Completo (Borrar todos los datos)

Si quieres empezar de cero:

```bash
# CUIDADO: Esto borra TODOS los datos de la base de datos
docker-compose down -v

# Re-inicializar desde cero
docker-compose up db -d
docker-compose --profile init run --rm init-db
docker-compose up backend
```

---

### Explicación de Servicios

El `docker-compose.yml` tiene 4 servicios, pero solo 2 corren por defecto:

| Servicio  | ¿Se levanta automáticamente? | Propósito                         |
| --------- | ---------------------------- | --------------------------------- |
| `db`      | SÍ                           | PostgreSQL (siempre activo)       |
| `backend` | SÍ                           | API Flask (siempre activo)        |
| `app`     | NO (profile: tools)          | Comandos manuales de Alembic      |
| `init-db` | NO (profile: init)           | Inicializar BD (solo primera vez) |

Los servicios con `profiles` solo se ejecutan cuando los invocas explícitamente.

## Migraciones de Base de Datos

Este proyecto usa **Alembic** para gestionar el schema de la base de datos.

### Desarrollo Local

Cuando modifiques modelos en `src/models/models.py`:

```bash
# Activar entorno virtual
source venv/bin/activate

# Generar migración automáticamente
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migración
alembic upgrade head
```

### Ver Estado de Migraciones

```bash
# Ver historial
alembic history

# Ver migración actual
alembic current
```

### Revertir Migración

```bash
# Revertir última migración
alembic downgrade -1

# Revertir a versión específica
alembic downgrade <revision_id>
```

### Con Docker (Opcional)

### Con Docker (Opcional)

Cuando modifiques modelos en `src/models/models.py`:

```bash
# Generar migración automáticamente
docker-compose run --rm app alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migración
docker-compose run --rm app alembic upgrade head
```

### Ver Estado de Migraciones (Docker)

```bash
# Ver historial
docker-compose run --rm app alembic history

# Ver migración actual
docker-compose run --rm app alembic current
```

### Revertir Migración (Docker)

```bash
# Revertir última migración
docker-compose run --rm app alembic downgrade -1

# Revertir a versión específica
docker-compose run --rm app alembic downgrade <revision_id>
```

## Datos Iniciales (Seed)

El archivo `src/db/seed.py` puebla la base de datos con:

- **Datos de Referencia**: Roles, Tipos de Local, Comunas, Tipos de Redes, Tipos de Fotos, Categorías
- **Datos de Ejemplo**: 5 Direcciones y 5 Locales de prueba

### Ejecutar Seed Manualmente

**Desarrollo Local:**
```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar seed
python src/db/seed.py
```

**Con Docker:**
```bash
docker-compose run --rm app python src/db/seed.py
```

El seed es **idempotente**: solo inserta datos que no existen.

## API Endpoints

### Health Check

```bash
GET /
```

Respuesta:

```json
{
  "status": "ok",
  "message": "Backend Flask funcionando correctamente"
}
```

### Locales

```bash
GET /locales
```

Retorna todos los locales.

Respuesta:

```json
[
  {
    "id": 1,
    "nombre": "El Gran Sabor",
    "telefono": 123456789,
    "correo": "contacto@gransabor.cl",
    "id_direccion": 1,
    "id_tipo_local": 1
  },
  ...
]
```

## Tecnologías

- **Flask** 3.0.3 - Framework web
- **SQLAlchemy** 2.0.29 - ORM
- **Alembic** 1.17.2 - Migraciones de BD
- **Pydantic** 2.12.4 - Validación de datos
- **PostgreSQL** 18 - Base de datos
- **Docker** - Contenedores

## Flujo de Inicialización

```mermaid
graph TD
    A[docker-compose up db] --> B[PostgreSQL inicia]
    B --> C{Healthcheck}
    C -->|Listo| D[docker-compose run init-db]
    D --> E[Alembic: crear tablas]
    E --> F[seed.py: poblar datos]
    F --> G[docker-compose up backend]
    G --> H[API en :5000]
```

## Notas

- **Alembic** gestiona el schema (tablas, columnas, índices)
- **Pydantic** valida datos de entrada/salida del API
- Todos los comandos usan Docker, no requiere instalación local
- Los datos se persisten en el volumen `pgdata` de Docker
- El backend se recarga automáticamente con cambios (hot-reload)

## Problemas Comunes

### Puerto 5432 en uso

Si PostgreSQL ya está corriendo en tu máquina y no puedes usar Docker:

```bash
# Detener PostgreSQL local (Linux)
sudo systemctl stop postgresql

# Detener PostgreSQL local (Windows)
Stop-Service postgresql

# O cambiar puerto en docker-compose.yml para Docker
ports:
  - "5433:5432"  # Usar puerto 5433 en host
```

Para desarrollo local, asegúrate de que PostgreSQL esté corriendo en el puerto 5432 o actualiza `DB_PORT` en tu archivo `.env`.

### Permisos en scripts/init_db.sh

```bash
# Dar permisos de ejecución (Linux/Mac)
chmod +x scripts/init_db.sh
```

### Errores de importación

**Desarrollo Local:**
Asegúrate de tener activado el entorno virtual y de ejecutar desde la raíz del proyecto:
```bash
source venv/bin/activate
export PYTHONPATH=/ruta/absoluta/al/proyecto/src
python src/main.py
```

**Con Docker:**
Asegúrate que `PYTHONPATH=/app/src` esté configurado en `docker-compose.yml`.

### Error: "No module named 'psycopg2'"

```bash
# Activar entorno virtual
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error de conexión a PostgreSQL

Verifica que PostgreSQL esté corriendo:

**Linux:**
```bash
sudo systemctl status postgresql
```

**macOS:**
```bash
brew services list
```

**Windows:**
Verifica en Servicios que PostgreSQL esté corriendo.

## Contacto

Para dudas o sugerencias, contacta al equipo de desarrollo.
