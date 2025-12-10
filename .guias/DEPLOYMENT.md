# Guía de Deployment - Backend RestoMap

Esta guía detalla cómo ejecutar el backend con Docker localmente y desplegarlo en Google Cloud Platform (GCP).

---

## Tabla de Contenidos

- [Prerequisitos](#prerequisitos)
- [Configuración Local con Docker](#configuración-local-con-docker)
- [Migraciones de Base de Datos](#migraciones-de-base-de-datos)
- [Deployment en GCP Cloud Run](#deployment-en-gcp-cloud-run)
- [Variables de Entorno](#variables-de-entorno)
- [Troubleshooting](#troubleshooting)

---

## Prerequisitos

### Software Requerido

- **Docker Desktop** 24.0+
- **Docker Compose** 2.20+
- **Poetry** 1.7+ (solo para desarrollo local sin Docker)
- **Google Cloud SDK** (para deployment en GCP)

### Cuenta GCP

- Proyecto de GCP creado
- Cloud SQL PostgreSQL instance configurada
- Cloud Run habilitado
- Permisos necesarios (Cloud Run Admin, Cloud SQL Client)

---

## Configuración Local con Docker

### 1. Clonar el repositorio

```bash
git clone https://github.com/Proyecto-SDS/back-RestoMap.git
cd back-RestoMap/backend
```

### 2. Configurar variables de entorno

Copia el archivo de ejemplo y edítalo:

```bash
cp .env.example .env
```

Edita `.env` con tus valores:

```env
# Entorno
ENV=dev
ALLOWED_ORIGINS=http://localhost:3000

# Base de Datos (Docker)
DB_USER=restomap_user
DB_PASSWORD=tu_password_seguro
DB_HOST=db
DB_PORT=5432
DB_NAME=restomap_db

# PostgreSQL (Docker Compose)
POSTGRES_USER=restomap_user
POSTGRES_PASSWORD=tu_password_seguro
POSTGRES_DB=restomap_db

# JWT
JWT_SECRET_KEY=dev-secret-key-change-in-production-2025
```

### 3. Iniciar servicios con Docker Compose

```bash
# Iniciar base de datos
docker-compose up -d db

# Esperar a que PostgreSQL esté listo (healthcheck automático)
docker-compose ps

# Inicializar base de datos y aplicar migraciones
docker-compose --profile init up init-db

# Iniciar backend
docker-compose up -d backend

# Ver logs
docker-compose logs -f backend
```

### 4. Verificar funcionamiento

```bash
# Health check
curl http://localhost:5000/health

# O abrir en navegador
http://localhost:5000/
```

### 5. Comandos útiles

```bash
# Detener todos los servicios
docker-compose down

# Reiniciar backend
docker-compose restart backend

# Ver logs en tiempo real
docker-compose logs -f backend

# Ejecutar migraciones manualmente
docker-compose --profile tools run app alembic upgrade head

# Crear nueva migración
docker-compose --profile tools run app alembic revision --autogenerate -m "descripcion"

# Acceder a shell del contenedor
docker-compose exec backend bash

# Limpiar todo (incluyendo volúmenes)
docker-compose down -v
```

---

## Migraciones de Base de Datos

### Desarrollo Local (Docker)

```bash
# Ver estado actual
docker-compose --profile tools run app alembic current

# Aplicar todas las migraciones
docker-compose --profile tools run app alembic upgrade head

# Crear nueva migración automática
docker-compose --profile tools run app alembic revision --autogenerate -m "nombre_descriptivo"

# Revertir última migración
docker-compose --profile tools run app alembic downgrade -1

# Ver historial
docker-compose --profile tools run app alembic history
```

### Producción (GCP Cloud Run)

El script `scripts/migrate_gcp.py` maneja las migraciones en producción:

```bash
# Ejecutar migraciones en Cloud Run
gcloud run jobs execute restomap-migrate \
  --region=us-central1 \
  --wait
```

O manualmente:

```bash
# Dentro del contenedor de Cloud Run
python scripts/migrate_gcp.py
```

---

## Deployment en GCP Cloud Run

### 1. Preparar Cloud SQL

```bash
# Crear instancia Cloud SQL PostgreSQL
gcloud sql instances create restomap-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Crear base de datos
gcloud sql databases create restomap_db \
  --instance=restomap-db

# Crear usuario
gcloud sql users create restomap_user \
  --instance=restomap-db \
  --password=PASSWORD_SEGURO
```

### 2. Configurar variables de entorno para GCP

Crea un archivo `.env.production`:

```env
ENV=production
ALLOWED_ORIGINS=https://tu-frontend.app

# Cloud SQL
DB_USER=restomap_user
DB_PASSWORD=tu_password_produccion
DB_HOST=/cloudsql/PROYECTO_ID:REGION:INSTANCE_NAME
DB_NAME=restomap_db

# JWT (CAMBIAR OBLIGATORIAMENTE)
JWT_SECRET_KEY=clave_super_segura_generada_aleatoriamente
```

### 3. Build y push de imagen

```bash
# Autenticar con GCP
gcloud auth configure-docker

# Build de imagen
docker build -t gcr.io/TU_PROYECTO_ID/restomap-backend:latest -f Dockerfile .

# Push a Container Registry
docker push gcr.io/TU_PROYECTO_ID/restomap-backend:latest
```

### 4. Deploy en Cloud Run

```bash
# Deploy del servicio
gcloud run deploy restomap-backend \
  --image gcr.io/TU_PROYECTO_ID/restomap-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances PROYECTO_ID:REGION:INSTANCE_NAME \
  --set-env-vars "ENV=production" \
  --set-env-vars "DB_USER=restomap_user" \
  --set-env-vars "DB_NAME=restomap_db" \
  --set-env-vars "DB_HOST=/cloudsql/PROYECTO_ID:REGION:INSTANCE_NAME" \
  --set-secrets "DB_PASSWORD=restomap-db-password:latest" \
  --set-secrets "JWT_SECRET_KEY=restomap-jwt-secret:latest" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0
```

### 5. Ejecutar migraciones en Cloud Run

Opción A: Cloud Run Job (Recomendado)

```bash
# Crear job de migración
gcloud run jobs create restomap-migrate \
  --image gcr.io/TU_PROYECTO_ID/restomap-backend:latest \
  --command python \
  --args scripts/migrate_gcp.py \
  --add-cloudsql-instances PROYECTO_ID:REGION:INSTANCE_NAME \
  --set-env-vars "DB_HOST=/cloudsql/PROYECTO_ID:REGION:INSTANCE_NAME" \
  --set-secrets "DB_PASSWORD=restomap-db-password:latest" \
  --region us-central1

# Ejecutar job
gcloud run jobs execute restomap-migrate --region=us-central1 --wait
```

Opción B: Cloud Run Service (temporal)

```bash
# SSH al servicio y ejecutar
gcloud run services proxy restomap-backend --port=8080
# En otro terminal
curl -X POST http://localhost:8080/admin/migrate
```

---

## Variables de Entorno

### Variables Requeridas

| Variable         | Descripción             | Ejemplo Local   | Ejemplo GCP                          |
| ---------------- | ----------------------- | --------------- | ------------------------------------ |
| `ENV`            | Entorno de ejecución    | `dev`           | `production`                         |
| `DB_USER`        | Usuario PostgreSQL      | `restomap_user` | `restomap_user`                      |
| `DB_PASSWORD`    | Contraseña PostgreSQL   | `password123`   | (Secret Manager)                     |
| `DB_HOST`        | Host de base de datos   | `db`            | `/cloudsql/proyecto:region:instance` |
| `DB_PORT`        | Puerto PostgreSQL       | `5432`          | - (no aplica para Unix socket)       |
| `DB_NAME`        | Nombre de base de datos | `restomap_db`   | `restomap_db`                        |
| `JWT_SECRET_KEY` | Clave secreta para JWT  | (dev key)       | (Secret Manager)                     |

### Variables Opcionales

| Variable          | Descripción              | Default                 |
| ----------------- | ------------------------ | ----------------------- |
| `PORT`            | Puerto del servidor      | `5000`                  |
| `ALLOWED_ORIGINS` | Orígenes CORS permitidos | `http://localhost:3000` |
| `PYTHONPATH`      | Path de módulos Python   | `/app/src`              |

---

## Troubleshooting

### Problema: Contenedor no inicia

```bash
# Ver logs detallados
docker-compose logs backend

# Verificar healthcheck
docker-compose ps

# Entrar al contenedor
docker-compose exec backend bash
```

### Problema: No puede conectar a la base de datos

```bash
# Verificar que PostgreSQL está corriendo
docker-compose ps db

# Probar conexión manual
docker-compose exec db psql -U restomap_user -d restomap_db

# Verificar variables de entorno
docker-compose exec backend env | grep DB_
```

### Problema: Migraciones fallan

```bash
# Ver estado de Alembic
docker-compose --profile tools run app alembic current

# Ver historial completo
docker-compose --profile tools run app alembic history

# Regenerar migraciones
docker-compose --profile tools run app alembic revision --autogenerate -m "fix"

# Downgrade y upgrade
docker-compose --profile tools run app alembic downgrade -1
docker-compose --profile tools run app alembic upgrade head
```

### Problema: Cloud Run no conecta a Cloud SQL

```bash
# Verificar instance connection name
gcloud sql instances describe INSTANCE_NAME | grep connectionName

# Verificar permisos
gcloud projects get-iam-policy PROYECTO_ID \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/cloudsql.client"

# Ver logs de Cloud Run
gcloud run services logs read restomap-backend --region=us-central1
```

### Problema: Error de permisos en Docker

```bash
# Linux/Mac: Dar permisos a scripts
chmod +x scripts/*.sh

# Reconstruir imagen sin cache
docker-compose build --no-cache backend
```

---

## Recursos Adicionales

- [Documentación Docker](https://docs.docker.com/)
- [Documentación Poetry](https://python-poetry.org/docs/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)

---

## Contribuir

Para contribuir al proyecto, consulta [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Licencia

[MIT License](../LICENSE)
