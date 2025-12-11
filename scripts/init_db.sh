#!/bin/bash
set -e
echo "Iniciando configuración de base de datos..."
echo "⏳ Esperando PostgreSQL..."
sleep 5
echo "Creando tablas..."
python src/init_tables.py
echo "Poblando datos iniciales..."
python src/db/seed.py
echo "Base de datos inicializada correctamente!"
