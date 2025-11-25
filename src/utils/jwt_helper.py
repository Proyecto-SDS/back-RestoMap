"""
Utilidades para manejo de JWT y autenticación
"""
import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

# Obtener clave secreta desde variables de entorno
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-key-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRATION_DAYS = 7


def crear_token(user_id: int, rol: str) -> str:
    """
    Crea un token JWT para el usuario
    
    Args:
        user_id: ID del usuario
        rol: Rol del usuario (usuario, dueno, administrador)
        
    Returns:
        Token JWT como string
    """
    payload = {
        'user_id': user_id,
        'rol': rol,
        'exp': datetime.utcnow() + timedelta(days=TOKEN_EXPIRATION_DAYS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(token: str) -> dict | None:
    """
    Verifica y decodifica un token JWT
    
    Args:
        token: Token JWT a verificar
        
    Returns:
        Payload del token si es válido, None si es inválido o expirado
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
    Decorator para proteger rutas que requieren autenticación
    
    Usage:
        @app.route('/api/protected')
        @requerir_auth
        def protected_route(user_id, user_rol):
            return {'message': f'Hola usuario {user_id}'}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Obtener token del header Authorization
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        # Verificar formato "Bearer {token}"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Formato de token inválido. Use: Bearer {token}'}), 401
        
        token = parts[1]
        
        # Verificar token
        payload = verificar_token(token)
        if not payload:
            return jsonify({'error': 'Token inválido o expirado'}), 401
        
        # Agregar user_id y user_rol al contexto de la función
        kwargs['user_id'] = payload['user_id']
        kwargs['user_rol'] = payload['rol']
        
        return f(*args, **kwargs)
    
    return decorated


def requerir_rol(*roles_permitidos):
    """
    Decorator para proteger rutas que requieren roles específicos
    
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
            user_rol = kwargs.get('user_rol')
            
            if user_rol not in roles_permitidos:
                return jsonify({
                    'error': 'No tiene permisos para acceder a este recurso',
                    'rol_requerido': list(roles_permitidos),
                    'rol_actual': user_rol
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator
