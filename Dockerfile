# ============================================
# DOCKERFILE OPTIMIZADO PARA GCP CLOUD RUN (CORREGIDO)
# ============================================

# STAGE 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configurar Poetry
ENV POETRY_HOME=/opt/poetry \
    PATH="/opt/poetry/bin:$PATH" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Instalar Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

COPY pyproject.toml poetry.lock ./

# Instalar dependencias
RUN --mount=type=cache,target=/tmp/poetry_cache \
    poetry install --no-root --only main --no-directory

# ============================================
# STAGE 2: Runtime
# ============================================
FROM python:3.12-slim

WORKDIR /app

# Instalar libpq5 (Vital para Postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar paquetes de Python desde el builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar el código
COPY alembic ./alembic
COPY alembic.ini pyproject.toml ./
COPY src ./src
# COPY scripts ./scripts  <-- Descomenta si usas scripts, si no, fallará si no existe la carpeta

# Crear usuario seguro
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# --- CORRECCIÓN CRÍTICA AQUÍ ---
# 1. PYTHONPATH debe ser /app para que gunicorn encuentre "src.main"
# 2. Agregamos /app/src también por si tienes imports internos que no usan "src."
ENV PORT=8080 \
    ENV=production \
    PYTHONPATH=/app:/app/src \
    PYTHONUNBUFFERED=1 \
    LOG_FORMAT=json

# Exponer puerto
EXPOSE ${PORT}

# Comando de arranque
CMD exec gunicorn \
    --bind 0.0.0.0:${PORT} \
    --workers 2 \
    --threads 4 \
    --timeout 0 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance \
    src.main:app