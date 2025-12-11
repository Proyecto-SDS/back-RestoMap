# Script para configurar el entorno de desarrollo local (sin Docker) en Windows

Write-Host "=========================================="
Write-Host "   Configuración de Desarrollo Local"
Write-Host "=========================================="
Write-Host ""

# Función para imprimir mensajes de éxito
function Write-Success {
    param($Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

# Función para imprimir mensajes de advertencia
function Write-Warning-Custom {
    param($Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# Función para imprimir mensajes de error
function Write-Error-Custom {
    param($Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# Verificar Python
Write-Host "Paso 1: Verificando Python..."
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python encontrado: $pythonVersion"
} catch {
    Write-Error-Custom "Python 3 no está instalado o no está en el PATH"
    Write-Host "Por favor instala Python 3.12 o superior desde https://www.python.org/"
    exit 1
}
Write-Host ""

# Verificar PostgreSQL
Write-Host "Paso 2: Verificando PostgreSQL..."
try {
    $psqlVersion = psql --version 2>&1
    Write-Success "PostgreSQL encontrado: $psqlVersion"
} catch {
    Write-Warning-Custom "PostgreSQL no está instalado o no está en el PATH"
    Write-Host "Por favor instala PostgreSQL 14 o superior desde https://www.postgresql.org/"
    Write-Host ""
    $continue = Read-Host "¿Deseas continuar de todos modos? (y/n)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}
Write-Host ""

# Crear entorno virtual
Write-Host "Paso 3: Creando entorno virtual..."
if (Test-Path "venv") {
    Write-Warning-Custom "El entorno virtual ya existe"
    $recreate = Read-Host "¿Deseas recrearlo? (y/n)"
    if ($recreate -eq "y" -or $recreate -eq "Y") {
        Remove-Item -Recurse -Force venv
        python -m venv venv
        Write-Success "Entorno virtual recreado"
    }
} else {
    python -m venv venv
    Write-Success "Entorno virtual creado"
}
Write-Host ""

# Activar entorno virtual
Write-Host "Paso 4: Activando entorno virtual..."
& "venv\Scripts\Activate.ps1"
Write-Success "Entorno virtual activado"
Write-Host ""

# Instalar dependencias
Write-Host "Paso 5: Instalando dependencias..."
python -m pip install --upgrade pip | Out-Null
pip install -r requirements.txt
Write-Success "Dependencias instaladas"
Write-Host ""

# Configurar .env
Write-Host "Paso 6: Configurando variables de entorno..."
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Success "Archivo .env creado desde .env.example"
    Write-Warning-Custom "Por favor edita .env con tus credenciales de base de datos"
} else {
    Write-Warning-Custom "El archivo .env ya existe, no se sobrescribirá"
}
Write-Host ""

# Instrucciones finales
Write-Host "=========================================="
Write-Host "   ¡Configuración Completada!"
Write-Host "=========================================="
Write-Host ""
Write-Host "Próximos pasos:"
Write-Host ""
Write-Host "1. Asegúrate de que PostgreSQL esté corriendo:"
Write-Host "   Verifica en Servicios de Windows o ejecuta:"
Write-Host "   Get-Service postgresql*"
Write-Host ""
Write-Host "2. Crea la base de datos (si no existe):"
Write-Host "   Abre pgAdmin o ejecuta en PowerShell:"
Write-Host "   psql -U postgres"
Write-Host "   CREATE USER tu_usuario WITH PASSWORD 'tu_contraseña';"
Write-Host "   CREATE DATABASE tu_bd OWNER tu_usuario;"
Write-Host "   GRANT ALL PRIVILEGES ON DATABASE tu_bd TO tu_usuario;"
Write-Host "   \quit"
Write-Host ""
Write-Host "3. Edita el archivo .env con tus credenciales"
Write-Host ""
Write-Host "4. Inicializa la base de datos:"
Write-Host "   venv\Scripts\Activate.ps1"
Write-Host "   .\scripts\init_db.ps1"
Write-Host ""
Write-Host "5. Ejecuta el backend:"
Write-Host "   venv\Scripts\Activate.ps1"
Write-Host "   python src\main.py"
Write-Host ""
Write-Host "Para desactivar el entorno virtual: deactivate"
Write-Host ""
