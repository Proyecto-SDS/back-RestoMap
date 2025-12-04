# Backend - Sistema de Gestión de Locales RestoMap

Sistema backend basado en Flask + SQLAlchemy + PostgreSQL para gestión de locales, pedidos y reservas.

🚀 **Optimizado para Docker y Google Cloud Platform (GCP Cloud Run)**

## 📋 Tabla de Contenido

- [Requisitos](#requisitos)
- [Inicio Rápido con Docker](#inicio-rápido-con-docker)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Configuración](#configuración)
- [Migraciones de Base de Datos](#migraciones-de-base-de-datos)
- [Deployment](#deployment)
- [API Endpoints](#api-endpoints)

## Requisitos

### Para Docker (Recomendado para Producción y Desarrollo)

- **Docker Desktop** 24.0+
- **Docker Compose** 2.20+

**✅ No se requiere instalación local de Python ni PostgreSQL** - todo se ejecuta en contenedores.

### Para Desarrollo Local sin Docker (Opcional)

- **Python 3.12.10**
- **Poetry 1.7+** (gestor de dependencias)
- **PostgreSQL 18** (opcional, puede usar solo la BD en Docker)

#### Instalación de Poetry

```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# Linux/macOS
curl -sSL https://install.python-poetry.org | python3 -
```

Ver la [Guía de Poetry](.guias/POETRY_GUIDE.md) para más información.

---

## 🚀 Inicio Rápido con Docker

```bash
# 1. Clonar repositorio
git clone https://github.com/Proyecto-SDS/back-RestoMap.git
cd back-RestoMap/backend

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 3. Iniciar base de datos
docker-compose up -d db

# 4. Inicializar base de datos (migraciones + seeds)
docker-compose --profile init up init-db

# 5. Iniciar backend
docker-compose up -d backend

# 6. Verificar funcionamiento
curl http://localhost:5000/health
```

**📖 Para deployment en GCP Cloud Run, ver [DEPLOYMENT.md](./DEPLOYMENT.md)**

---

## Desarrollo Local con Poetry

### Instalación de dependencias

```bash
# Configurar Poetry para crear el entorno en el proyecto
poetry config virtualenvs.in-project true

# Instalar todas las dependencias
poetry install
```

### Ejecutar la aplicación localmente

```bash
# Asegúrate de tener PostgreSQL corriendo (Docker o local)
docker-compose up db -d

# Ejecutar el servidor
poetry run python src/main.py
```

### Herramientas de desarrollo

```bash
# Linter y formateador (Ruff)
poetry run ruff check .
poetry run ruff format .

# Type checker (Pyrefly)
poetry run pyrefly check
```

Para más comandos y detalles, consulta la [Guía de Poetry](.guias/POETRY_GUIDE.md).

## Configuracion

### 1. Variables de Entorno

Copia el archivo `.env.example` a `.env`:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
# Base de Datos
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_HOST=localhost       # 'db' en Docker
DB_PORT=5432
DB_NAME=tu_bd

# PostgreSQL (Docker)
POSTGRES_USER=tu_usuario
POSTGRES_PASSWORD=tu_contraseña
POSTGRES_DB=tu_bd

# Configuracion General
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001 # Lista separada por comas
ENV=development # 'production' o 'development'
```

## Produccion con Docker

El proyecto incluye un `Dockerfile` optimizado para produccion que utiliza **Gunicorn** como servidor WSGI.

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

> **Nota:** En produccion (GCP), no uses `docker-compose` para el despliegue del backend. Usa esta imagen individual conectada a una instancia de Cloud SQL.

## Uso con Docker

### Primera Vez - Paso a Paso

#### Paso 1: Configurar Variables de Entorno

Asegúrate de tener tu archivo `.env` configurado (ver seccion [Configuracion](#configuracion)).

#### Paso 2: Construir Imagenes Docker

```bash
# Construir las imagenes de Docker (primera vez)
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

Espera hasta que veas `(healthy)` - esto significa que el healthcheck paso.

#### Paso 5: Inicializar la Base de Datos

```bash
# Crear tablas con Alembic y poblar datos iniciales
docker-compose --profile init run --rm init-db
```

**Qué hace:**

1. Genera migracion inicial de Alembic
2. Crea todas las tablas en PostgreSQL
3. Ejecuta `seed.py` para insertar datos de referencia (roles, comunas, etc.)
4. Inserta 5 locales de ejemplo

**Salida esperada:**

```
Iniciando configuracion de base de datos...
Generando migracion inicial...
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

### Explicacion de Servicios

El `docker-compose.yml` tiene 4 servicios, pero solo 2 corren por defecto:

| Servicio  | ¿Se levanta automaticamente? | Proposito                         |
| --------- | ---------------------------- | --------------------------------- |
| `db`      | Si                           | PostgreSQL (siempre activo)       |
| `backend` | Si                           | API Flask (siempre activo)        |
| `app`     | NO (profile: tools)          | Comandos manuales de Alembic      |
| `init-db` | NO (profile: init)           | Inicializar BD (solo primera vez) |

Los servicios con `profiles` solo se ejecutan cuando los invocas explicitamente.

## Migraciones de Base de Datos

Este proyecto usa **Alembic** para gestionar el schema de la base de datos.

### Crear una Migracion

Cuando modifiques modelos en `src/models/models.py`:

```bash
# Generar migracion automaticamente
docker-compose run --rm app alembic revision --autogenerate -m "Descripcion del cambio"

# Aplicar migracion
docker-compose run --rm app alembic upgrade head
```

### Ver Estado de Migraciones

```bash
# Ver historial
docker-compose run --rm app alembic history

# Ver migracion actual
docker-compose run --rm app alembic current
```

### Revertir Migracion

```bash
# Revertir última migracion
docker-compose run --rm app alembic downgrade -1

# Revertir a version especifica
docker-compose run --rm app alembic downgrade <revision_id>
```

## Datos Iniciales (Seed)

El archivo `src/db/seed.py` puebla la base de datos con:

- **Datos de Referencia**: Roles, Tipos de Local, Comunas, Tipos de Redes, Tipos de Fotos, Categorias
- **Datos de Ejemplo**: 5 Direcciones y 5 Locales de prueba

### Ejecutar Seed Manualmente

```bash
# Dentro de Docker
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

## Tecnologias

### Backend

- **Flask** 3.1.2 - Framework web
- **SQLAlchemy** 2.0.44 - ORM
- **Alembic** 1.17.2 - Migraciones de BD
- **Pydantic** 2.12.5 - Validacion de datos
- **PostgreSQL** 18 - Base de datos
- **Gunicorn** 23.0.0 - Servidor WSGI para producción

### Herramientas de Desarrollo

- **Poetry** - Gestión de dependencias
- **Ruff** 0.14.8 - Linter y formateador
- **Pyrefly** 0.44.1 - Type checker estático

### Infraestructura

- **Docker** - Contenedores
- **Docker Compose** - Orquestación

## Flujo de Inicializacion

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

- **Alembic** gestiona el schema (tablas, columnas, indices)
- **Pydantic** valida datos de entrada/salida del API
- Todos los comandos usan Docker, no requiere instalacion local
- Los datos se persisten en el volumen `pgdata` de Docker
- El backend se recarga automaticamente con cambios (hot-reload)

## Problemas Comunes

### Puerto 5432 en uso

Si PostgreSQL ya esta corriendo en tu maquina:

```bash
# Detener PostgreSQL local (Windows)
Stop-Service postgresql

# O cambiar puerto en docker-compose.yml
ports:
  - "5433:5432"  # Usar puerto 5433 en host
```

### Permisos en scripts/init_db.sh

```bash
# Dar permisos de ejecucion (Linux/Mac)
chmod +x scripts/init_db.sh
```

### Errores de importacion

Asegúrate que `PYTHONPATH=/app/src` esté configurado en `docker-compose.yml`.

## Contacto

Para dudas o sugerencias, contacta al equipo de desarrollo.
