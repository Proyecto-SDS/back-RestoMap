"""
Módulo de rutas - Exporta todos los blueprints
"""
from .locales import locales_bp
from .auth import auth_bp
from .opiniones import opiniones_bp
from .reservas import reservas_bp
from .favoritos import favoritos_bp

__all__ = [
    'locales_bp',
    'auth_bp',
    'opiniones_bp',
    'reservas_bp',
    'favoritos_bp'
]
