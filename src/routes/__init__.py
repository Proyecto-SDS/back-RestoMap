"""
Módulo de rutas - Exporta todos los blueprints
"""

from .auth import auth_bp
from .favoritos import favoritos_bp
from .locales import locales_bp
from .opiniones import opiniones_bp
from .reservas import reservas_bp

__all__ = ["auth_bp", "favoritos_bp", "locales_bp", "opiniones_bp", "reservas_bp"]
