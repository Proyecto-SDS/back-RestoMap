# Script de inicializacion de base de datos para Windows (desarrollo local)
# Este script crea las tablas con Alembic y luego pobla datos iniciales

Write-Host "Iniciando configuracion de base de datos..." -ForegroundColor Cyan

# Verificar que las variables de entorno estén cargadas
if (-not $env:DB_HOST) {
    Write-Host "Variables de entorno no encontradas. Cargando desde .env..." -ForegroundColor Yellow
    
    if (Test-Path ".\.env") {
        Get-Content ".\.env" | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]+)=(.+)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                Set-Item -Path "env:$name" -Value $value
                Write-Host "  ✓ $name cargado" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "Archivo .env no encontrado!" -ForegroundColor Red
        exit 1
    }
}

# Crear migracion inicial si no existe
if (-not (Test-Path "alembic\versions\*.py")) {
    Write-Host "Generando migracion inicial..." -ForegroundColor Yellow
    alembic revision --autogenerate -m "Migracion inicial"
}

# Ejecutar migraciones
Write-Host "Aplicando migraciones de base de datos..." -ForegroundColor Yellow
alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error al aplicar migraciones!" -ForegroundColor Red
    exit 1
}

# Poblar datos iniciales
Write-Host "Poblando datos iniciales..." -ForegroundColor Yellow
python src\db\seed.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error al poblar datos!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Base de datos inicializada correctamente!" -ForegroundColor Green
