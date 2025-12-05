"""
Blueprint principal para rutas de empresa/paneles
Prefix: /api/empresa/*
"""

from functools import wraps

from flask import Blueprint, jsonify

empresa_bp = Blueprint("empresa", __name__, url_prefix="/api/empresa")


def requerir_empleado(f):
    """
    Decorator para verificar que el usuario es empleado de un local.
    Debe usarse DESPUES de @requerir_auth
    
    Valida que:
    - El usuario tiene id_local asignado
    - El usuario tiene un rol de empleado
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        id_local = kwargs.get("id_local")
        user_rol = kwargs.get("user_rol")

        if id_local is None:
            return jsonify({"error": "Acceso denegado. Solo empleados pueden acceder"}), 403

        if user_rol is None:
            return jsonify({"error": "Usuario sin rol asignado"}), 403

        return f(*args, **kwargs)

    return decorated


def requerir_roles_empresa(*roles_permitidos):
    """
    Decorator para verificar roles de empresa.
    Debe usarse DESPUES de @requerir_auth y @requerir_empleado
    
    Args:
        *roles_permitidos: Roles que pueden acceder (ej: 'gerente', 'mesero', 'cocinero', 'bartender')
    
    Usage:
        @empresa_bp.route('/empleados')
        @requerir_auth
        @requerir_empleado
        @requerir_roles_empresa('gerente')
        def get_empleados(user_id, user_rol, id_local):
            return {'empleados': []}
    """

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_rol = kwargs.get("user_rol")

            if user_rol not in roles_permitidos:
                return jsonify(
                    {
                        "error": "No tiene permisos para acceder a este recurso",
                        "roles_permitidos": list(roles_permitidos),
                        "rol_actual": user_rol,
                    }
                ), 403

            return f(*args, **kwargs)

        return decorated

    return decorator


# Importar sub-blueprints
from routes.empresa.mesas import mesas_bp
from routes.empresa.pedidos import pedidos_bp
from routes.empresa.empleados import empleados_bp
from routes.empresa.productos import productos_bp
from routes.empresa.stats import stats_bp

# Registrar sub-blueprints
empresa_bp.register_blueprint(mesas_bp)
empresa_bp.register_blueprint(pedidos_bp)
empresa_bp.register_blueprint(empleados_bp)
empresa_bp.register_blueprint(productos_bp)
empresa_bp.register_blueprint(stats_bp)
