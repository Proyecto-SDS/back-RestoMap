# Guía de Uso de Ruff

## ¿Qué es Ruff?

Ruff es un linter y formatter extremadamente rápido para Python, escrito en Rust. Combina la funcionalidad de múltiples herramientas (Flake8, Black, isort, pyupgrade, etc.) en una sola herramienta unificada.

**Velocidad**: 10-100x más rápido que herramientas tradicionales
**Funcionalidad**: Más de 800 reglas de linting disponibles
**Integración**: Compatible con Black y otras herramientas populares

## Instalación

Ruff ya está instalado en el proyecto. Para instalarlo en otros entornos:

```bash
# Dentro del entorno virtual
pip install -r requirements.txt

# O instalación individual
pip install ruff==0.14.8
```

## Configuración

La configuración de Ruff está en el archivo `ruff.toml` en la raíz del proyecto.

### Reglas Activadas

- **F (Pyflakes)**: Errores básicos de Python
- **E/W (pycodestyle)**: Errores y advertencias de estilo
- **I (isort)**: Ordenamiento de imports
- **N (pep8-naming)**: Convenciones de nombres
- **UP (pyupgrade)**: Modernización de código Python
- **B (flake8-bugbear)**: Búsqueda de bugs comunes
- **SIM (flake8-simplify)**: Simplificación de código
- **C90 (mccabe)**: Complejidad ciclomática
- **ARG (flake8-unused-arguments)**: Argumentos sin usar
- **PTH (flake8-use-pathlib)**: Uso de pathlib
- **PL (Pylint)**: Reglas de Pylint
- **RUF (Ruff-specific)**: Reglas específicas de Ruff

## Comandos Principales

### Linting

```bash
# Verificar todo el código en src/
ruff check src

# Verificar un archivo específico
ruff check src/main.py

# Auto-corregir errores
ruff check src --fix

# Mostrar todos los errores (incluso los que se pueden auto-corregir)
ruff check src --show-fixes

# Aplicar fixes inseguros (con precaución)
ruff check src --fix --unsafe-fixes
```

### Formatting

```bash
# Formatear todo el código en src/
ruff format src

# Formatear un archivo específico
ruff format src/main.py

# Verificar formato sin modificar archivos
ruff format src --check

# Ver diferencias sin aplicar cambios
ruff format src --diff
```

### Combinando Lint + Format

```bash
# Primero formatear, luego lintear
ruff format src && ruff check src --fix
```

## Integración con VSCode

La configuración de VSCode ya está lista en `.vscode/settings.json`:

- **Auto-fix al guardar**: Los errores se corrigen automáticamente
- **Auto-format al guardar**: El código se formatea automáticamente
- **Organización de imports**: Los imports se ordenan al guardar

### Instalar Extensión de Ruff (Opcional)

Para una mejor integración, puedes instalar la extensión oficial de Ruff:

1. Abre VSCode
2. Ve a la pestaña de Extensiones (Ctrl+Shift+X)
3. Busca "Ruff"
4. Instala "Ruff" por Astral Software

**ID de la extensión**: `charliermarsh.ruff`

## Ignorar Reglas Específicas

### En archivo de configuración (ruff.toml)

```toml
[lint]
ignore = [
    "E501",    # Line too long
    "PLR0913", # Too many arguments
]
```

### En el código (comentarios)

```python
# Ignorar una regla en una línea específica
x = 1  # noqa: F841

# Ignorar múltiples reglas
def foo():  # noqa: ARG001, PLR0913
    pass

# Ignorar toda la verificación en un archivo
# ruff: noqa

# Ignorar reglas en un bloque
# ruff: noqa: F401
from typing import List
from typing import Dict
# ruff: noqa
```

## Casos de Uso Comunes

### Verificar antes de hacer commit

```bash
ruff check src --fix && ruff format src
```

### CI/CD Pipeline

```bash
# En tu pipeline de integración continua
ruff check src --output-format=github
ruff format src --check
```

### Pre-commit Hook

Puedes agregar Ruff a tu pre-commit hook:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.8
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

## Errores Comunes y Soluciones

### W293: Blank line contains whitespace

**Solución**: Se corrige automáticamente con `ruff check --fix`

### PLC0415: Import should be at top-level

**Solución**: Mover los imports al inicio del archivo o agregar `# noqa: PLC0415` si es necesario que estén dentro de una función

### UP035: typing.X is deprecated

**Solución**: Usar tipos built-in de Python 3.9+ (ej: `list` en lugar de `typing.List`)

### ARG001: Unused function argument

**Solución**:

- Eliminar el argumento si no se usa
- Prefijarlo con `_` si es intencional: `_user_rol`
- Ignorar con `# noqa: ARG001`

## Estado Actual del Proyecto

**Última ejecución**: Diciembre 4, 2025

- 542 errores corregidos automáticamente
- 23 archivos reformateados
- 142 errores pendientes (requieren revisión manual)
- Total de archivos analizados: 26

### Errores Pendientes Principales

1. **PLC0415**: Imports dentro de funciones (múltiples archivos)
2. **W293**: Líneas en blanco con espacios (en docstrings)
3. **ARG001**: Argumentos de función sin usar
4. **SIM108**: Oportunidades para usar operador ternario

## Recursos Adicionales

- [Documentación Oficial](https://docs.astral.sh/ruff/)
- [Reglas Disponibles](https://docs.astral.sh/ruff/rules/)
- [Configuración](https://docs.astral.sh/ruff/configuration/)
- [GitHub](https://github.com/astral-sh/ruff)

## Comandos Útiles de Referencia Rápida

```bash
# Ver versión
ruff --version

# Ver ayuda
ruff --help
ruff check --help
ruff format --help

# Generar configuración de ejemplo
ruff check --show-settings

# Listar todas las reglas disponibles
ruff rule --all

# Ver información de una regla específica
ruff rule F401
```

## Notas Importantes

1. **Compatibilidad con Black**: Ruff está configurado para ser compatible con Black (line-length=88)
2. **Python Target**: Configurado para Python 3.11
3. **Auto-fixes Seguros**: Por defecto, Ruff solo aplica fixes que considera seguros
4. **Formato de Docstrings**: Activado el formateo de código en docstrings
5. **Complejidad Máxima**: Configurada en 10 (mccabe)

## Mantenimiento

Para mantener Ruff actualizado:

```bash
pip install --upgrade ruff
```

Luego actualiza `requirements.txt` con la nueva versión.
