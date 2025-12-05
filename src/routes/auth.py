"""
Rutas de autenticacion
Endpoints: /api/auth/*
"""

# pyrefly: ignore [missing-import]
import bcrypt
from flask import Blueprint, jsonify
from pydantic import ValidationError
from sqlalchemy import select

from config import get_logger
from database import SessionLocal
from models.models import Local, Rol, Usuario
from schemas import LoginSchema, ProfileUpdateSchema, RegisterSchema
from utils.jwt_helper import crear_token, requerir_auth
from utils.validation import validate_json

logger = get_logger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def get_db():
    """Obtener sesion de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@auth_bp.route("/login", methods=["POST"])
@validate_json(LoginSchema)
def login(data: LoginSchema):
    """
    Iniciar sesion con correo y contrasena

    Detecta automaticamente si es persona o empleado:
    - Persona: rol=null, id_local=null
    - Empleado: rol y id_local presentes

    Body:
        {
            "correo": "usuario@example.com",
            "contrasena": "password123",
            "tipo_login": "persona" | "empresa"
        }

    Response 200 (Persona):
        {
            "success": true,
            "token": "eyJhbGc...",
            "user": {
                "id": "1",
                "nombre": "Juan Perez",
                "correo": "usuario@example.com",
                "telefono": "+56912345678",
                "creado_el": "2024-01-01T12:00:00"
            }
        }

    Response 200 (Empleado):
        {
            "success": true,
            "token": "eyJhbGc...",
            "user": {
                "id": "2",
                "nombre": "Maria Mesera",
                "correo": "mesero@test.cl",
                "telefono": "+56912345678",
                "rol": "mesero",
                "id_local": 1,
                "nombre_local": "RestoMap Central",
                "creado_el": "2024-01-01T12:00:00"
            }
        }

    Response 400:
        {"error": "Datos invalidos", "details": [...]}
        {"error": "Cuenta de empleado sin local asignado"}
        {"error": "Cuenta de empleado sin rol asignado"}

    Response 401:
        {"error": "Correo o contrasena incorrectos"}

    Response 404:
        {"error": "Local no encontrado"}
    """
    try:
        correo = data.correo.lower()
        contrasena = data.contrasena
        tipo_login = data.tipo_login

        db = next(get_db())

        # Buscar usuario por correo
        usuario = db.execute(
            select(Usuario).options().where(Usuario.correo == correo)
        ).scalar_one_or_none()

        if not usuario:
            return jsonify({"error": "Correo o contrasena incorrectos"}), 401

        # Verificar contrasena con bcrypt
        if not bcrypt.checkpw(
            contrasena.encode("utf-8"), usuario.contrasena.encode("utf-8")
        ):
            return jsonify({"error": "Correo o contrasena incorrectos"}), 401

        # VALIDACION: Verificar que el tipo de login coincida con el tipo de cuenta
        es_empleado = usuario.id_local is not None

        if tipo_login == "persona" and es_empleado:
            return jsonify(
                {
                    "error": "Esta es una cuenta de empleado. Por favor usa el tab 'Empresa' para iniciar sesion"
                }
            ), 400

        if tipo_login == "empresa" and not es_empleado:
            return jsonify(
                {
                    "error": "Esta es una cuenta de persona. Por favor usa el tab 'Persona' para iniciar sesion"
                }
            ), 400

        # VALIDACION: Verificar coherencia de datos
        # Si tiene id_local, DEBE tener id_rol (empleado)
        if usuario.id_local is not None and usuario.id_rol is None:
            logger.error(
                f"Usuario {usuario.id} tiene id_local pero no id_rol (datos inconsistentes)"
            )
            return jsonify({"error": "Cuenta de empleado sin rol asignado"}), 400

        # Formatear telefono
        telefono_formateado = f"+56{usuario.telefono}" if usuario.telefono else None

        # CASO 1: Usuario Persona/Cliente (id_local=null, id_rol deberia ser "cliente")
        if usuario.id_local is None:
            # Obtener el nombre del rol si existe
            rol_nombre = None
            if usuario.id_rol:
                rol_persona = db.execute(
                    select(Rol).where(Rol.id == usuario.id_rol)
                ).scalar_one_or_none()
                rol_nombre = rol_persona.nombre if rol_persona else None

            # Crear token con rol "cliente" (o el rol que tenga) pero sin id_local
            token = crear_token(usuario.id, rol_nombre, None)

            return (
                jsonify(
                    {
                        "success": True,
                        "token": token,
                        "user": {
                            "id": str(usuario.id),
                            "nombre": usuario.nombre,
                            "correo": usuario.correo,
                            "telefono": telefono_formateado,
                            "rol": rol_nombre,  # Incluir rol en la respuesta (deberia ser "cliente")
                            "creado_el": usuario.creado_el.isoformat()
                            if usuario.creado_el
                            else None,
                        },
                    }
                ),
                200,
            )

        # CASO 2: Usuario Empleado (tiene id_local y debe tener id_rol)
        # Obtener rol del empleado
        rol = db.execute(
            select(Rol).where(Rol.id == usuario.id_rol)
        ).scalar_one_or_none()

        if not rol:
            logger.error(
                f"Usuario {usuario.id} tiene id_rol={usuario.id_rol} pero el rol no existe"
            )
            return jsonify({"error": "Rol de empleado no encontrado"}), 404

        rol_nombre = rol.nombre

        # Obtener informacion del Local (VERIFICAR EN BD antes de crear token)
        local = db.execute(
            select(Local).where(Local.id == usuario.id_local)
        ).scalar_one_or_none()

        if not local:
            logger.error(
                f"Usuario {usuario.id} tiene id_local={usuario.id_local} pero el local no existe"
            )
            return jsonify({"error": "Local no encontrado"}), 404

        # Crear token CON rol y id_local (empleado verificado)
        token = crear_token(usuario.id, rol_nombre, usuario.id_local)

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
                    "id_local": usuario.id_local,
                    "nombre_local": local.nombre,
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
@validate_json(RegisterSchema)
def register(data: RegisterSchema):
    """
    Registrar nuevo usuario

    Body:
        {
            "nombre": "Juan Perez",
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
        {"error": "Datos invalidos", "details": [...]}
        {"error": "Este correo ya esta registrado"}
    """
    try:
        nombre = data.nombre.strip()
        correo = data.correo.lower()
        contrasena = data.contrasena
        telefono_limpio = data.telefono  # Ya viene limpio del schema

        db = next(get_db())

        # Verificar si el correo ya existe
        usuario_existente = db.execute(
            select(Usuario).where(Usuario.correo == correo)
        ).scalar_one_or_none()

        if usuario_existente:
            return jsonify({"error": "Este correo ya esta registrado"}), 400

        # Hash de contrasena con bcrypt
        hashed_password = bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt())

        # Obtener rol "cliente" para usuarios normales (personas)
        rol_cliente = db.execute(
            select(Rol).where(Rol.nombre == "cliente")
        ).scalar_one_or_none()

        # Fallback: usar id 6 si no existe rol_cliente (basado en seed: cliente es el 6to rol)
        rol_id = 6 if not rol_cliente else rol_cliente.id

        # Crear nuevo usuario (persona/cliente sin id_local)
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

    except ValidationError as e:
        return jsonify({"error": "Datos invalidos", "details": e.errors()}), 400
    except Exception as e:
        logger.error(f"Error en register: {e!s}")
        return jsonify({"error": "Error al procesar la solicitud"}), 500


@auth_bp.route("/logout", methods=["POST"])
@requerir_auth
def logout(user_id=None, user_rol=None, id_local=None):  # noqa: ARG001
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
            "nombre": "Juan Perez",
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

        # Formatear telefono
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
@validate_json(ProfileUpdateSchema)
def update_profile(data: ProfileUpdateSchema, user_id, user_rol):
    """
    Actualizar perfil del usuario autenticado

    Headers:
        Authorization: Bearer {token}

    Body:
        {
            "nombre": "Juan Perez Actualizado",
            "telefono": "987654321"
        }

    Response 200:
        {
            "success": true,
            "message": "Perfil actualizado exitosamente",
            "user": {
                "id": "1",
                "nombre": "Juan Perez Actualizado",
                "correo": "usuario@example.com",
                "telefono": "+56987654321",
                "rol": "usuario"
            }
        }

    Response 400:
        {"error": "Datos invalidos", "details": [...]}
    """
    try:
        nombre = data.nombre
        telefono = data.telefono  # Ya viene limpio del schema

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
            usuario.nombre = nombre.strip()

        # Actualizar telefono si se proporciona
        if telefono:
            usuario.telefono = int(telefono)

        db.commit()

        # Formatear telefono para respuesta
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
