"""
Configuracion centralizada de logging para la aplicacion.

Este modulo proporciona:
- Configuracion consistente en todo el proyecto
- Niveles configurables por entorno
- Formato estructurado para GCP Cloud Logging (JSON)
- Formato legible para desarrollo local
- Rotacion de logs opcional
- Compatibilidad con Docker y GCP Cloud Run
"""

import logging
import logging.handlers
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar, Literal

# Tipos
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Mapeo de niveles para GCP Cloud Logging
# https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#LogSeverity
GCP_SEVERITY_MAP = {
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "WARNING": "WARNING",
    "ERROR": "ERROR",
    "CRITICAL": "CRITICAL",
}


class GCPFormatter(logging.Formatter):
    """
    Formatter compatible con Google Cloud Logging.

    Produce logs en formato JSON que GCP Cloud Logging puede parsear
    automaticamente, incluyendo:
    - severity: Nivel del log (compatible con GCP)
    - message: Mensaje del log
    - timestamp: Marca de tiempo ISO 8601
    - logging.googleapis.com/sourceLocation: Ubicacion en el codigo

    Referencia:
    https://cloud.google.com/logging/docs/structured-logging
    """

    def format(self, record: logging.LogRecord) -> str:
        import json

        # Estructura compatible con GCP Cloud Logging
        log_entry = {
            "severity": GCP_SEVERITY_MAP.get(record.levelname, "DEFAULT"),
            "message": record.getMessage(),
            "timestamp": datetime.now(UTC).isoformat(),
            "logging.googleapis.com/sourceLocation": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            },
            "logger": record.name,
        }

        # Agregar exception info si existe
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            log_entry["severity"] = "ERROR"

        # Agregar trace si existe (para correlacion de requests en GCP)
        if hasattr(record, "trace"):
            # pyrefly: ignore  # missing-attribute
            log_entry["logging.googleapis.com/trace"] = record.trace

        # Agregar request_id si existe
        if hasattr(record, "request_id"):
            # pyrefly: ignore  # missing-attribute
            log_entry["httpRequest"] = {"requestId": record.request_id}

        # Agregar user_id si existe
        if hasattr(record, "user_id"):
            # pyrefly: ignore  # missing-attribute
            log_entry["labels"] = {"user_id": str(record.user_id)}

        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Formatter con colores para desarrollo local.
    Solo para uso en desarrollo, NO usar en produccion/GCP.

    Colorea:
    - Niveles de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Metodos HTTP (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
    """

    # Colores ANSI
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Colores para niveles de log
    LEVEL_COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Verde
        "WARNING": "\033[33m",  # Amarillo
        "ERROR": "\033[31m",  # Rojo
        "CRITICAL": "\033[35m",  # Magenta
    }

    # Colores para metodos HTTP
    HTTP_COLORS: ClassVar[dict[str, str]] = {
        "GET": "\033[32m",  # Verde
        "POST": "\033[34m",  # Azul
        "PUT": "\033[33m",  # Amarillo
        "PATCH": "\033[36m",  # Cyan
        "DELETE": "\033[31m",  # Rojo
        "HEAD": "\033[35m",  # Magenta
        "OPTIONS": "\033[37m",  # Blanco
    }

    def format(self, record: logging.LogRecord) -> str:
        # Colorear nivel de log
        level_color = self.LEVEL_COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{level_color}{record.levelname}{self.RESET}"

        # Colorear metodos HTTP en el mensaje
        message = record.getMessage()
        for method, color in self.HTTP_COLORS.items():
            # Buscar el metodo HTTP como palabra completa
            if method in message:
                colored_method = f"{self.BOLD}{color}{method}{self.RESET}"
                message = message.replace(method, colored_method)

        # Reemplazar el mensaje con la version coloreada
        record.msg = message
        record.args = ()

        return super().format(record)


def is_running_in_gcp() -> bool:
    """
    Detecta si la aplicacion esta corriendo en GCP.
    Cloud Run y otros servicios GCP definen ciertas variables de entorno.
    """
    gcp_indicators = [
        "K_SERVICE",  # Cloud Run
        "K_REVISION",  # Cloud Run
        "GOOGLE_CLOUD_PROJECT",  # GCP general
        "GCP_PROJECT",  # GCP alternativo
        "GAE_APPLICATION",  # App Engine
        "FUNCTION_NAME",  # Cloud Functions
    ]
    return any(os.getenv(var) for var in gcp_indicators)


def is_running_in_docker() -> bool:
    """Detecta si la aplicacion esta corriendo en Docker."""
    # Metodo 1: Verificar archivo .dockerenv
    if Path("/.dockerenv").exists():
        return True

    # Metodo 2: Verificar cgroup (Linux)
    try:
        with Path("/proc/1/cgroup").open() as f:
            return "docker" in f.read()
    except (FileNotFoundError, PermissionError):
        pass

    return False


def get_log_level() -> int:
    """
    Obtiene el nivel de logging desde variables de entorno.
    Default: INFO en produccion/GCP, DEBUG en desarrollo.
    """
    env = os.getenv("FLASK_ENV", os.getenv("ENV", "development"))

    # En GCP, default a INFO para evitar exceso de logs
    if is_running_in_gcp():
        default_level = "INFO"
    elif env == "development":
        default_level = "DEBUG"
    else:
        default_level = "INFO"

    level_name = os.getenv("LOG_LEVEL", default_level).upper()

    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    return level_map.get(level_name, logging.INFO)


def get_formatter() -> logging.Formatter:
    """
    Retorna el formatter apropiado segun el entorno.
    - GCP/Docker/Produccion: Formato JSON estructurado para Cloud Logging
    - Desarrollo local: Formato con colores, legible
    """
    env = os.getenv("FLASK_ENV", os.getenv("ENV", "development"))
    log_format = os.getenv("LOG_FORMAT", "auto")  # auto, json, text

    # Forzar JSON si se especifica o si estamos en GCP/Docker/produccion
    use_json = (
        log_format == "json"
        or is_running_in_gcp()
        or (log_format == "auto" and env == "production")
        or (log_format == "auto" and is_running_in_docker())
    )

    if use_json:
        return GCPFormatter()

    # Desarrollo local: formato legible con colores
    format_string = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Usar colores solo si stdout soporta ANSI (no en archivos o CI/CD)
    if sys.stdout.isatty():
        return ColoredFormatter(format_string, datefmt=date_format)

    return logging.Formatter(format_string, datefmt=date_format)


def setup_logging(
    level: LogLevel | None = None,
    log_file: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    Configura el sistema de logging para toda la aplicacion.

    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Si es None, se obtiene de LOG_LEVEL env var.
        log_file: Path opcional para escribir logs a archivo.
                  Si es None, se obtiene de LOG_FILE env var.
                  NOTA: En GCP Cloud Run, los logs van a stdout automaticamente.
        max_bytes: Tamano maximo del archivo de log antes de rotar (default 10MB).
        backup_count: Numero de archivos de backup a mantener (default 5).

    Variables de entorno soportadas:
        LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL
        LOG_FILE: Path al archivo de logs (opcional)
        LOG_FORMAT: auto, json, text

    Uso:
        from config import setup_logging

        # En main.py (llamar una sola vez al inicio)
        setup_logging()
    """
    # Determinar nivel
    log_level = getattr(logging, level) if level else get_log_level()

    # Determinar archivo de log (no recomendado en GCP, usar stdout)
    log_file = log_file or os.getenv("LOG_FILE")

    # Obtener formatter
    formatter = get_formatter()

    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Limpiar handlers existentes (evita duplicados en reloads)
    root_logger.handlers.clear()

    # Handler para consola (stdout - requerido para GCP Cloud Logging)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Handler para archivo (opcional, no recomendado en GCP/Docker)
    if log_file and not is_running_in_gcp():
        log_path = Path(log_file)
        if log_path.parent:
            log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(GCPFormatter())  # JSON en archivo
        root_logger.addHandler(file_handler)

    # Silenciar loggers ruidosos de terceros
    noisy_loggers = [
        "urllib3",
        "werkzeug",
        "sqlalchemy.engine",
        "httpcore",
        "httpx",
        "googleapiclient",
        "google.auth",
        "engineio",
        "socketio",
        "eventlet",
        "eventlet.wsgi",
        "gevent",
        "geventwebsocket",
    ]
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Log inicial con info del entorno
    logger = logging.getLogger(__name__)
    env_info = []
    if is_running_in_gcp():
        env_info.append("GCP")
    if is_running_in_docker():
        env_info.append("Docker")
    env_str = "/".join(env_info) if env_info else "Local"

    logger.info(
        f"Logging configurado: level={logging.getLevelName(log_level)}, "
        f"env={env_str}, format={'JSON' if isinstance(formatter, GCPFormatter) else 'text'}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado.

    Uso:
        from config import get_logger

        logger = get_logger(__name__)
        logger.info("Mensaje")
        logger.error("Error", exc_info=True)

    Args:
        name: Nombre del logger (normalmente __name__)

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


# Alias conveniente
Logger = get_logger
