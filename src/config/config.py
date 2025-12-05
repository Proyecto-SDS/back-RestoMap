import logging
import os

# Usar logging.getLogger directamente aqui porque este modulo
# se importa antes de que setup_logging() sea llamado
logger = logging.getLogger(__name__)


class Config:
    """Clase de configuracion centralizada"""

    # Configuracion general
    JSON_SORT_KEYS = False
    JSON_AS_ASCII = False  # Permite caracteres UTF-8 en JSON

    # CORS
    ALLOWED_ORIGINS = os.environ.get(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001"
    ).split(",")

    # Servidor
    PORT = int(os.environ.get("PORT", "5000"))
    ENV = os.environ.get("ENV", "production")
    DEBUG = ENV in ["dev", "development"]

    # Seguridad
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    @classmethod
    def validate(cls) -> None:
        """Valida que las variables criticas estén configuradas"""
        if not cls.JWT_SECRET_KEY:
            logger.warning(
                "JWT_SECRET_KEY no está configurado. Usando valor por defecto."
            )

        if cls.ENV == "production" and cls.DEBUG:
            logger.warning("DEBUG está activado en produccion. Esto es peligroso.")

        if (
            cls.ENV == "production"
            and cls.JWT_SECRET_KEY == "dev-secret-key-change-in-production-2025"
        ):
            logger.error("CRiTICO: Usando clave JWT de desarrollo en produccion!")
            raise ValueError("JWT_SECRET_KEY debe ser cambiado en produccion")
