#!/bin/bash
# Script para configurar el entorno de desarrollo local (sin Docker)

set -e

echo "=========================================="
echo "   Configuración de Desarrollo Local"
echo "=========================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para imprimir mensajes de éxito
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Función para imprimir mensajes de advertencia
warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Función para imprimir mensajes de error
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Verificar Python
echo "Paso 1: Verificando Python..."
if ! command -v python3 &> /dev/null; then
    error "Python 3 no está instalado"
    echo "Por favor instala Python 3.12 o superior"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
success "Python encontrado: $PYTHON_VERSION"
echo ""

# Verificar PostgreSQL
echo "Paso 2: Verificando PostgreSQL..."
if ! command -v psql &> /dev/null; then
    warning "PostgreSQL no está instalado o no está en el PATH"
    echo "Por favor instala PostgreSQL 14 o superior"
    echo "Consulta el README.md para instrucciones de instalación"
    echo ""
    read -p "¿Deseas continuar de todos modos? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    POSTGRES_VERSION=$(psql --version)
    success "PostgreSQL encontrado: $POSTGRES_VERSION"
fi
echo ""

# Crear entorno virtual
echo "Paso 3: Creando entorno virtual..."
if [ -d "venv" ]; then
    warning "El entorno virtual ya existe"
    read -p "¿Deseas recrearlo? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        success "Entorno virtual recreado"
    fi
else
    python3 -m venv venv
    success "Entorno virtual creado"
fi
echo ""

# Activar entorno virtual
echo "Paso 4: Activando entorno virtual..."
source venv/bin/activate
success "Entorno virtual activado"
echo ""

# Instalar dependencias
echo "Paso 5: Instalando dependencias..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
success "Dependencias instaladas"
echo ""

# Configurar .env
echo "Paso 6: Configurando variables de entorno..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    success "Archivo .env creado desde .env.example"
    warning "Por favor edita .env con tus credenciales de base de datos"
else
    warning "El archivo .env ya existe, no se sobrescribirá"
fi
echo ""

# Instrucciones finales
echo "=========================================="
echo "   ¡Configuración Completada!"
echo "=========================================="
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Asegúrate de que PostgreSQL esté corriendo:"
echo "   Linux: sudo systemctl status postgresql"
echo "   macOS: brew services list"
echo ""
echo "2. Crea la base de datos (si no existe):"
echo "   sudo -u postgres psql"
echo "   CREATE USER tu_usuario WITH PASSWORD 'tu_contraseña';"
echo "   CREATE DATABASE tu_bd OWNER tu_usuario;"
echo "   GRANT ALL PRIVILEGES ON DATABASE tu_bd TO tu_usuario;"
echo "   \\q"
echo ""
echo "3. Edita el archivo .env con tus credenciales"
echo ""
echo "4. Inicializa la base de datos:"
echo "   source venv/bin/activate"
echo "   ./scripts/init_db.sh"
echo ""
echo "5. Ejecuta el backend:"
echo "   source venv/bin/activate"
echo "   python src/main.py"
echo ""
echo "Para desactivar el entorno virtual: deactivate"
echo ""
