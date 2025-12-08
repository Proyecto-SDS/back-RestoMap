# ============================================
# DOCKERFILE OPTIMIZADO PARA GCP CLOUD RUN
# Multi-stage build para minimizar tamano
# ============================================

# ============================================
# STAGE 1: Builder
# Instala dependencias y prepara el entorno
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
ENV POETRY_HOME=/opt/poetry
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 -

# Configurar Poetry para no crear virtualenv (usaremos el sistema)
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copiar archivos de dependencias
COPY pyproject.toml poetry.lock ./

# Instalar solo dependencias de produccion (sin dev)
RUN --mount=type=cache,target=/tmp/poetry_cache \
    poetry install --no-root --only main --no-directory

# ============================================
# STAGE 2: Runtime
# Imagen final optimizada para produccion
# ============================================
FROM python:3.12-slim

# Metadatos
LABEL maintainer="Proyecto SDS"
LABEL description="Backend RestoMap - Sistema de Gestion de Restaurantes"
LABEL version="1.0.0"

WORKDIR /app

# Instalar solo dependencias runtime necesarias (libpq para PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar dependencias Python desde builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar codigo de la aplicacion
COPY alembic ./alembic
COPY alembic.ini pyproject.toml ./
COPY src ./src
COPY scripts ./scripts

RUN grep -F "app.register_blueprint(locales_bp)" src/main.py && echo "!!! ALERTA: DOCKER ESTA VIENDO EL CODIGO VIEJO !!!" && exit 1 || echo ">>> EXITO: No se encontró la línea vieja."

# Crear usuario no-root para seguridad (requerido por Cloud Run)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Variables de entorno para Python y la app
ENV PORT=8080 \
    ENV=production \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Variables para GCP Cloud Logging
    LOG_FORMAT=json

# Health check usando curl (mas ligero que python)
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Exponer puerto (Cloud Run usa PORT env var, default 8080)
EXPOSE ${PORT}

# Comando para ejecutar con Gunicorn + Eventlet
# Usar forma JSON y expansión de shell para garantizar que la variable
# `PORT` se evalúe en tiempo de ejecución y tenga un fallback a 8080.
# Esto evita problemas cuando la imagen anterior no tenía PORT o Cloud Run
# no la inyectó correctamente.
CMD ["sh", "-c", "exec gunicorn \
    --bind 0.0.0.0:${PORT:-8080} \
    --worker-class eventlet \
    --workers 1 \
    --timeout 0 \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance \
    src.main:app"]
