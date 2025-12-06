"""
Utilidades para manejo de JWT y autenticacion
"""

import os
from datetime import datetime, timedelta
from functools import wraps

# pyrefly: ignore [missing-import]
import jwt
from flask import jsonify, request

# Obtener clave secreta desde variables de entorno
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-key-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRATION_DAYS = 7


def crear_token(user_id: int, rol: str | None, id_local: int | None = None) -> str:
    """
    Crea un token JWT para el usuario

    Args:
        user_id: ID del usuario
        rol: Rol del usuario (usuario, admin, mesero, chef, etc.) o None para personas
        id_local: ID del local para empleados, None para personas

    Returns:
        Token JWT como string
    """
    payload = {
        "user_id": user_id,
        "rol": rol,
        "id_local": id_local,
        # pyrefly: ignore [deprecated]
        "exp": datetime.utcnow() + timedelta(days=TOKEN_EXPIRATION_DAYS),
        # pyrefly: ignore [deprecated]
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(token: str) -> dict | None:
    """
    Verifica y decodifica un token JWT

    Args:
        token: Token JWT a verificar

    Returns:
        Payload del token si es valido, None si es invalido o expirado
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def requerir_auth(f):
    """
    Decorator para proteger rutas que requieren autenticacion

    IMPORTANTE: Este decorator VALIDA que los datos del JWT (id_local, id_rol)
    coincidan con los datos reales del usuario en la base de datos.
    Esto previene ataques de manipulacion del JWT.

    Usage:
        @app.route('/api/protected')
        @requerir_auth
        def protected_route(user_id, user_rol, id_local):
            return {'message': f'Hola usuario {user_id}'}
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        from database import get_db
        from models.models import Usuario

        # Obtener token del header Authorization
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Token no proporcionado"}), 401

        # Verificar formato "Bearer {token}"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify(
                {"error": "Formato de token invalido. Use: Bearer {token}"}
            ), 401

        token = parts[1]

        # Verificar token
        payload = verificar_token(token)
        if not payload:
            return jsonify({"error": "Token invalido o expirado"}), 401

        user_id = payload["user_id"]
        jwt_rol = payload.get("rol")
        jwt_id_local = payload.get("id_local")

        # VALIDACION CONTRA BASE DE DATOS
        db = next(get_db())
        try:
            usuario = db.query(Usuario).filter(Usuario.id == user_id).first()

            if not usuario:
                return jsonify({"error": "Usuario no encontrado"}), 401

            # Obtener rol real desde la base de datos
            rol_real = usuario.rol.nombre if usuario.rol else None
            id_local_real = usuario.id_local

            # VALIDAR QUE LOS DATOS DEL JWT COINCIDAN CON LA BD
            if jwt_rol != rol_real:
                return jsonify(
                    {
                        "error": "Token invalido: el rol ha sido modificado",
                        "detalle": "Los datos del token no coinciden con la base de datos",
                    }
                ), 401

            if jwt_id_local != id_local_real:
                return jsonify(
                    {
                        "error": "Token invalido: el local ha sido modificado",
                        "detalle": "Los datos del token no coinciden con la base de datos",
                    }
                ), 401

            # Usar los valores REALES de la base de datos, no los del JWT
            kwargs["user_id"] = user_id
            kwargs["user_rol"] = rol_real
            kwargs["id_local"] = id_local_real

        finally:
            db.close()

        return f(*args, **kwargs)

    return decorated


def requerir_auth_persona(f):
    """
    Decorator para proteger rutas que requieren autenticacion de usuario.

    Todos los usuarios registrados son clientes, independientemente de si
    tienen un rol de empleado (gerente, mesero, chef, etc.).

    IMPORTANTE: Este decorator VALIDA que los datos del JWT (id_local, id_rol)
    coincidan con los datos reales del usuario en la base de datos.

    Usage:
        @app.route('/api/favoritos/')
        @requerir_auth_persona
        def get_favoritos(user_id):
            return {'favoritos': []}
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        from database import get_db
        from models.models import Usuario

        # Obtener token del header Authorization
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Token no proporcionado"}), 401

        # Verificar formato "Bearer {token}"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify(
                {"error": "Formato de token invalido. Use: Bearer {token}"}
            ), 401

        token = parts[1]

        # Verificar token
        payload = verificar_token(token)
        if not payload:
            return jsonify({"error": "Token invalido o expirado"}), 401

        user_id = payload["user_id"]
        jwt_id_local = payload.get("id_local")

        # VALIDACION CONTRA BASE DE DATOS
        db = next(get_db())
        try:
            usuario = db.query(Usuario).filter(Usuario.id == user_id).first()

            if not usuario:
                return jsonify({"error": "Usuario no encontrado"}), 401

            id_local_real = usuario.id_local

            # VALIDAR QUE EL JWT NO HAYA SIDO MANIPULADO
            if jwt_id_local != id_local_real:
                return jsonify(
                    {
                        "error": "Token invalido: los datos han sido modificados",
                        "detalle": "Los datos del token no coinciden con la base de datos",
                    }
                ), 401

            # Todos los usuarios registrados son clientes (con o sin rol de empleado)
            # Solo pasar user_id
            kwargs["user_id"] = user_id

        finally:
            db.close()

        return f(*args, **kwargs)

    return decorated


def requerir_rol(*roles_permitidos):
    """
    Decorator para proteger rutas que requieren roles especificos

    Args:
        *roles_permitidos: Roles que pueden acceder (ej: 'dueno', 'administrador')

    Usage:
        @app.route('/api/admin')
        @requerir_auth
        @requerir_rol('administrador')
        def admin_route(user_id, user_rol):
            return {'message': 'Acceso de administrador'}
    """

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_rol = kwargs.get("user_rol")

            if user_rol not in roles_permitidos:
                return jsonify(
                    {
                        "error": "No tiene permisos para acceder a este recurso",
                        "rol_requerido": list(roles_permitidos),
                        "rol_actual": user_rol,
                    }
                ), 403

            return f(*args, **kwargs)

        return decorated

    return decorator
