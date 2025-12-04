# Usar una imagen base oficial de Python ligera
FROM python:3.12-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2 y otras librerias
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Configurar Poetry para no crear entornos virtuales (usamos el del contenedor)
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Copiar archivos de configuración de Poetry
COPY pyproject.toml poetry.lock ./

# Instalar solo dependencias de producción (sin dev)
RUN poetry install --no-root --only main

# Copiar el codigo de la aplicacion
COPY . .

# Establecer variables de entorno por defecto
ENV PORT=5000
ENV ENV=production
ENV PYTHONPATH=/app/src

# Exponer el puerto
EXPOSE 5000

# Comando para ejecutar la aplicacion usando Gunicorn (Servidor de Produccion)
# Ajusta 'src.main:app' si tu estructura es diferente.
# 'src.main' es el modulo (archivo main.py dentro de carpeta src)
# 'app' es la instancia de Flask dentro de ese archivo.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "src.main:app"]
