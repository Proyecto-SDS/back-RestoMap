# ============================================
# DOCKERFILE OPTIMIZADO PARA PRODUCCIÓN
# Multi-stage build para minimizar tamaño
# ============================================

# ============================================
# STAGE 1: Builder
# Instala dependencias y prepara el entorno
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Configurar Poetry
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copiar archivos de dependencias
COPY pyproject.toml poetry.lock ./

# Instalar solo dependencias de producción
RUN --mount=type=cache,target=/tmp/poetry_cache \
    poetry install --no-root --only main

# ============================================
# STAGE 2: Runtime
# Imagen final optimizada
# ============================================
FROM python:3.12-slim

# Metadatos
LABEL maintainer="Proyecto SDS"
LABEL description="Backend RestoMap - Sistema de Gestión de Restaurantes"

WORKDIR /app

# Instalar solo dependencias runtime necesarias
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias Python desde builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar código de la aplicación
COPY alembic ./alembic
COPY alembic.ini pyproject.toml ./
COPY src ./src

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Variables de entorno
ENV PORT=5000 \
    ENV=production \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=2)" || exit 1

# Exponer puerto
EXPOSE 5000

# Comando para ejecutar con Gunicorn
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "src.main:app"]
