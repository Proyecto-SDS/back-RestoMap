#!/bin/bash
# Script de inicializacion de base de datos para Docker
# Este script crea las tablas con Alembic y luego pobla datos iniciales

set -e  # Salir si algún comando falla

echo "Iniciando configuracion de base de datos..."

# Esperar a que PostgreSQL esté listo (redundante con healthcheck, pero seguro)
echo "⏳ Esperando PostgreSQL..."
sleep 2

# Crear migracion inicial si no existe
if [ ! -d "alembic/versions" ] || [ -z "$(ls -A alembic/versions)" ]; then
    echo "Generando migracion inicial..."
    alembic revision --autogenerate -m "Migracion inicial"
fi

# Ejecutar migraciones
echo "Aplicando migraciones de base de datos..."
alembic upgrade head

# Poblar datos iniciales
echo "Poblando datos iniciales..."
python src/db/seed.py

echo "Base de datos inicializada correctamente!"
