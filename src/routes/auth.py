"""
Rutas de autenticacion
Endpoints: /api/auth/*
"""

import logging

# pyrefly: ignore [missing-import]
import bcrypt
from flask import Blueprint, jsonify, request
from sqlalchemy import select

from database import SessionLocal
from models.models import Rol, Usuario
from utils.jwt_helper import crear_token, requerir_auth

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def get_db():
    """Obtener sesion de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Iniciar sesion con correo y contraseña

    Body:
        {
            "correo": "usuario@example.com",
            "contrasena": "password123"
        }

    Response 200:
        {
            "success": true,
            "token": "eyJhbGc...",
            "user": {
                "id": "1",
                "nombre": "Juan Pérez",
                "correo": "usuario@example.com",
                "telefono": "+56912345678",
                "rol": "usuario",
                "creado_el": "2024-01-01T12:00:00"
            }
        }

    Response 400:
        {"error": "Correo y contraseña son requeridos"}

    Response 401:
        {"error": "Correo o contraseña incorrectos"}
    """
    try:
        data = request.get_json()

        correo = data.get("correo", "").strip().lower()
        contrasena = data.get("contrasena", "")

        if not correo or not contrasena:
            return jsonify({"error": "Correo y contraseña son requeridos"}), 400

        db = next(get_db())

        # Buscar usuario por correo
        usuario = db.execute(
            select(Usuario).options().where(Usuario.correo == correo)
        ).scalar_one_or_none()

        if not usuario:
            return jsonify({"error": "Correo o contraseña incorrectos"}), 401

        # Verificar contraseña con bcrypt
        if not bcrypt.checkpw(
            contrasena.encode("utf-8"), usuario.contrasena.encode("utf-8")
        ):
            return jsonify({"error": "Correo o contraseña incorrectos"}), 401

        # Obtener rol
        rol = db.execute(
            select(Rol).where(Rol.id == usuario.id_rol)
        ).scalar_one_or_none()

        rol_nombre = rol.nombre if rol else "usuario"

        # Crear token JWT
        token = crear_token(usuario.id, rol_nombre)

        # Formatear teléfono
        telefono_formateado = f"+56{usuario.telefono}" if usuario.telefono else None

        # Respuesta exitosa
        return jsonify(
            {
                "success": True,
                "token": token,
                "user": {
                    "id": str(usuario.id),
                    "nombre": usuario.nombre,
                    "correo": usuario.correo,
                    "telefono": telefono_formateado,
                    "rol": rol_nombre,
                    "creado_el": usuario.creado_el.isoformat()
                    if usuario.creado_el
                    else None,
                },
            }
        ), 200

    except Exception as e:
        logger.error(f"Error en login: {e!s}")
        return jsonify({"error": "Error al procesar la solicitud"}), 500


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Registrar nuevo usuario

    Body:
        {
            "nombre": "Juan Pérez",
            "correo": "usuario@example.com",
            "contrasena": "password123",
            "telefono": "912345678"
        }

    Response 201:
        {
            "success": true,
            "message": "Usuario registrado exitosamente"
        }

    Response 400:
        {"error": "Todos los campos son requeridos"}
        {"error": "Este correo ya esta registrado"}
    """
    try:
        data = request.get_json()

        nombre = data.get("nombre", "").strip()
        correo = data.get("correo", "").strip().lower()
        contrasena = data.get("contrasena", "")
        telefono = data.get("telefono", "").strip()

        # Validar campos requeridos
        if not nombre or not correo or not contrasena or not telefono:
            return jsonify({"error": "Todos los campos son requeridos"}), 400

        # Validar longitud de contraseña
        if len(contrasena) < 6:
            return jsonify(
                {"error": "La contraseña debe tener al menos 6 caracteres"}
            ), 400

        # Limpiar teléfono (remover +56 si existe)
        telefono_limpio = telefono.replace("+56", "").replace(" ", "").replace("-", "")
        if not telefono_limpio.isdigit() or len(telefono_limpio) != 9:
            return jsonify({"error": "Teléfono invalido. Debe tener 9 digitos"}), 400

        db = next(get_db())

        # Verificar si el correo ya existe
        usuario_existente = db.execute(
            select(Usuario).where(Usuario.correo == correo)
        ).scalar_one_or_none()

        if usuario_existente:
            return jsonify({"error": "Este correo ya esta registrado"}), 400

        # Hash de contraseña con bcrypt
        hashed_password = bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt())

        # Obtener rol "usuario" (asumir id=3 basado en seed)
        rol_usuario = db.execute(
            select(Rol).where(Rol.nombre == "usuario")
        ).scalar_one_or_none()

        # Fallback: usar id 3 si no existe rol_usuario
        rol_id = 3 if not rol_usuario else rol_usuario.id

        # Crear nuevo usuario
        nuevo_usuario = Usuario(
            nombre=nombre,
            correo=correo,
            contrasena=hashed_password.decode("utf-8"),
            telefono=int(telefono_limpio),
            id_rol=rol_id,
        )

        db.add(nuevo_usuario)
        db.commit()

        return jsonify(
            {"success": True, "message": "Usuario registrado exitosamente"}
        ), 201

    except Exception as e:
        logger.error(f"Error en register: {e!s}")
        return jsonify({"error": "Error al procesar la solicitud"}), 500


@auth_bp.route("/logout", methods=["POST"])
@requerir_auth
def logout(_user_id, _user_rol):
    """
    Cerrar sesion (actualmente solo responde exitosamente)

    En el futuro se puede implementar blacklist de tokens

    Headers:
        Authorization: Bearer {token}

    Response 200:
        {"success": true, "message": "Sesion cerrada"}
    """
    return jsonify({"success": True, "message": "Sesion cerrada exitosamente"}), 200


@auth_bp.route("/profile", methods=["GET"])
@requerir_auth
def get_profile(user_id, user_rol):
    """
    Obtener perfil del usuario autenticado

    Headers:
        Authorization: Bearer {token}

    Response 200:
        {
            "id": "1",
            "nombre": "Juan Pérez",
            "correo": "usuario@example.com",
            "telefono": "+56912345678",
            "rol": "usuario",
            "creado_el": "2024-01-01T12:00:00"
        }

    Response 404:
        {"error": "Usuario no encontrado"}
    """
    try:
        db = next(get_db())

        # Buscar usuario
        usuario = db.execute(
            select(Usuario).where(Usuario.id == user_id)
        ).scalar_one_or_none()

        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # Formatear teléfono
        telefono_formateado = f"+56{usuario.telefono}" if usuario.telefono else None

        return jsonify(
            {
                "id": str(usuario.id),
                "nombre": usuario.nombre,
                "correo": usuario.correo,
                "telefono": telefono_formateado,
                "rol": user_rol,
                "creado_el": usuario.creado_el.isoformat()
                if usuario.creado_el
                else None,
            }
        ), 200

    except Exception as e:
        logger.error(f"Error en get_profile: {e!s}")
        return jsonify({"error": "Error al procesar la solicitud"}), 500


@auth_bp.route("/profile", methods=["PUT"])
@requerir_auth
def update_profile(user_id, user_rol):
    """
    Actualizar perfil del usuario autenticado

    Headers:
        Authorization: Bearer {token}

    Body:
        {
            "nombre": "Juan Pérez Actualizado",
            "telefono": "987654321"
        }

    Response 200:
        {
            "success": true,
            "message": "Perfil actualizado exitosamente",
            "user": {
                "id": "1",
                "nombre": "Juan Pérez Actualizado",
                "correo": "usuario@example.com",
                "telefono": "+56987654321",
                "rol": "usuario"
            }
        }

    Response 400:
        {"error": "Teléfono invalido"}
    """
    try:
        data = request.get_json()

        nombre = data.get("nombre", "").strip()
        telefono = data.get("telefono", "").strip()

        if not nombre and not telefono:
            return jsonify(
                {"error": "Debe proporcionar al menos un campo para actualizar"}
            ), 400

        db = next(get_db())

        # Buscar usuario
        usuario = db.execute(
            select(Usuario).where(Usuario.id == user_id)
        ).scalar_one_or_none()

        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # Actualizar nombre si se proporciona
        if nombre:
            usuario.nombre = nombre

        # Actualizar teléfono si se proporciona
        if telefono:
            telefono_limpio = (
                telefono.replace("+56", "").replace(" ", "").replace("-", "")
            )
            if not telefono_limpio.isdigit() or len(telefono_limpio) != 9:
                return jsonify(
                    {"error": "Teléfono invalido. Debe tener 9 digitos"}
                ), 400
            usuario.telefono = int(telefono_limpio)

        db.commit()

        # Formatear teléfono para respuesta
        telefono_formateado = f"+56{usuario.telefono}" if usuario.telefono else None

        return jsonify(
            {
                "success": True,
                "message": "Perfil actualizado exitosamente",
                "user": {
                    "id": str(usuario.id),
                    "nombre": usuario.nombre,
                    "correo": usuario.correo,
                    "telefono": telefono_formateado,
                    "rol": user_rol,
                },
            }
        ), 200

    except Exception as e:
        logger.error(f"Error en update_profile: {e!s}")
        return jsonify({"error": "Error al procesar la solicitud"}), 500
