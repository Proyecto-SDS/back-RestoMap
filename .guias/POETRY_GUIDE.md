# Guía de uso de Poetry

## ¿Qué es Poetry?

Poetry es una herramienta moderna de gestión de dependencias y empaquetado para Python que:

- Simplifica la gestión de dependencias
- Crea y gestiona entornos virtuales automáticamente
- Resuelve conflictos de dependencias de forma inteligente
- Genera archivos `poetry.lock` para garantizar instalaciones reproducibles

## Configuración del proyecto

### Entorno virtual

Poetry está configurado para crear el entorno virtual dentro del proyecto (`.venv/`):

```bash
poetry config virtualenvs.in-project true
```

### Versión de Python

Este proyecto usa **Python 3.12.10** como se especifica en `pyproject.toml`.

## Comandos básicos

### Instalación de dependencias

```bash
# Instalar todas las dependencias del proyecto
poetry install

# Instalar solo dependencias de producción (sin dev)
poetry install --only main

# Instalar solo dependencias de desarrollo
poetry install --only dev
```

### Gestión de dependencias

```bash
# Agregar una nueva dependencia de producción
poetry add nombre-paquete

# Agregar con versión específica
poetry add nombre-paquete@^2.0.0

# Agregar dependencia de desarrollo
poetry add --group dev nombre-paquete

# Eliminar una dependencia
poetry remove nombre-paquete

# Actualizar todas las dependencias
poetry update

# Actualizar una dependencia específica
poetry update nombre-paquete

# Ver todas las dependencias instaladas
poetry show

# Ver árbol de dependencias
poetry show --tree
```

### Ejecución de comandos

```bash
# Activar el entorno virtual
poetry shell

# Ejecutar comando sin activar el entorno
poetry run python src/main.py

# Ejecutar Ruff
poetry run ruff check .

# Ejecutar Pyrefly
poetry run pyrefly check
```

### Información del entorno

```bash
# Ver información del entorno virtual
poetry env info

# Ver ruta del entorno virtual
poetry env info --path

# Listar todos los entornos virtuales del proyecto
poetry env list
```

### Gestión del archivo lock

```bash
# Actualizar poetry.lock sin instalar
poetry lock

# Actualizar poetry.lock sin actualizar dependencias
poetry lock --no-update

# Verificar que poetry.lock está sincronizado con pyproject.toml
poetry check
```

## Estructura del pyproject.toml

```toml
[tool.poetry]
name = "restomap-backend"
version = "0.1.0"
description = "Backend del sistema RestoMap - Gestión de restaurantes"
authors = ["Proyecto SDS"]
readme = "README.md"
package-mode = false  # No empaquetamos, solo gestionamos dependencias

[tool.poetry.dependencies]
python = "^3.12.10"
# Dependencias de producción
flask = "^3.1.2"
sqlalchemy = "^2.0.44"
# ... etc

[tool.poetry.group.dev.dependencies]
# Dependencias solo para desarrollo
ruff = "^0.14.8"
pyrefly = "^0.44.1"
```

## Dependencias del proyecto

### Producción

Todas las dependencias necesarias para ejecutar la aplicación:

- **Flask**: Framework web
- **SQLAlchemy**: ORM para base de datos
- **Alembic**: Migraciones de base de datos
- **Pydantic**: Validación de datos
- **psycopg2-binary**: Driver de PostgreSQL
- **PyJWT**: Autenticación JWT
- **bcrypt**: Hashing de contraseñas
- Y más...

### Desarrollo

Herramientas solo para desarrollo:

- **Ruff**: Linter y formateador de código
- **Pyrefly**: Type checker estático

## Workflows comunes

### Agregar nueva funcionalidad con dependencia

```bash
# 1. Agregar la dependencia
poetry add requests

# 2. Usar en el código
# from requests import get

# 3. El archivo poetry.lock se actualiza automáticamente
```

### Actualizar una dependencia específica

```bash
# Ver versión actual
poetry show flask

# Actualizar a la última versión compatible
poetry update flask

# Ver nueva versión
poetry show flask
```

### Exportar dependencias a requirements.txt (si es necesario)

```bash
# Exportar solo producción
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Exportar incluyendo dev
poetry export -f requirements.txt --output requirements.txt --with dev --without-hashes
```

### Sincronizar dependencias después de git pull

```bash
# Si alguien actualizó poetry.lock
poetry install

# Si solo actualizó pyproject.toml
poetry lock
poetry install
```

## Integración con VSCode

El entorno virtual de Poetry (`.venv/`) es detectado automáticamente por VSCode.

### Seleccionar el intérprete de Python:

1. `Ctrl + Shift + P`
2. "Python: Select Interpreter"
3. Seleccionar `./.venv/Scripts/python.exe`

### Configuración en `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/Scripts/python.exe",
  "python.terminal.activateEnvironment": true
}
```

## Diferencias con pip + requirements.txt

| Característica             | pip + requirements.txt | Poetry                  |
| -------------------------- | ---------------------- | ----------------------- |
| Gestión de dependencias    | Manual                 | Automática              |
| Resolución de conflictos   | No                     | Sí                      |
| Entornos virtuales         | Manual (venv)          | Automático              |
| Archivo de lock            | No estándar            | poetry.lock             |
| Dependencias de desarrollo | Separar archivos       | Grupos integrados       |
| Actualización selectiva    | Difícil                | `poetry update paquete` |

## Solución de problemas

### El entorno virtual no se detecta

```bash
# Recrear el entorno
poetry env remove python
poetry install
```

### Conflictos de dependencias

```bash
# Ver el árbol de dependencias
poetry show --tree

# Forzar actualización
poetry update
```

### poetry.lock desactualizado

```bash
# Regenerar el lock file
poetry lock --no-update
poetry install
```

### Limpiar caché de Poetry

```bash
poetry cache clear pypi --all
```

## Comandos útiles adicionales

```bash
# Ver configuración de Poetry
poetry config --list

# Cambiar configuración
poetry config virtualenvs.in-project true

# Ver versión de Poetry
poetry --version

# Ayuda de cualquier comando
poetry help
poetry help add
```

## Mejores prácticas

1. **Siempre commits `poetry.lock`** - Garantiza instalaciones reproducibles
2. **Usa grupos para dependencias de desarrollo** - Mantén separadas las dependencias
3. **Actualiza regularmente** - `poetry update` para mantener dependencias al día
4. **Verifica antes de commit** - `poetry check` para validar el pyproject.toml

## Recursos adicionales

- Documentación oficial: https://python-poetry.org/docs/
- Especificación de dependencias: https://python-poetry.org/docs/dependency-specification/
- Gestión de entornos: https://python-poetry.org/docs/managing-environments/
