"""
Rutas de autenticacion
Endpoints: /api/auth/*
"""

# pyrefly: ignore [missing-import]
import contextlib
from datetime import datetime

import bcrypt
from flask import Blueprint, jsonify
from pydantic import ValidationError
from sqlalchemy import select

from config import get_logger
from database import SessionLocal
from models.models import Direccion, Local, Rol, Usuario
from schemas import LoginSchema, ProfileUpdateSchema, RegisterSchema
from schemas.auth import RegisterEmpresaSchema
from services.rut_service import (
    consultar_rut_sre,
    validar_digito_verificador,
    validar_formato_rut,
)
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
        # tipo_login ya no se usa - login unificado

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

        # VALIDACION: Verificar coherencia de datos
        # Si tiene id_local, DEBE tener id_rol (empleado)
        if usuario.id_local is not None and usuario.id_rol is None:
            logger.error(
                f"Usuario {usuario.id} tiene id_local pero no id_rol (datos inconsistentes)"
            )
            return jsonify({"error": "Cuenta de empleado sin rol asignado"}), 400

        # Formatear telefono
        telefono_formateado = f"+56{usuario.telefono}" if usuario.telefono else None

        # CASO 1: Usuario Persona/Cliente (id_local=null, id_rol=null)
        if usuario.id_local is None:
            # Los clientes tienen id_rol=None
            # Solo verificamos por si acaso hay algun usuario legacy con id_rol
            rol_nombre = None
            if usuario.id_rol:
                rol_persona = db.execute(
                    select(Rol).where(Rol.id == usuario.id_rol)
                ).scalar_one_or_none()
                rol_nombre = rol_persona.nombre if rol_persona else None

            # Crear token con rol=None para clientes (sin id_local)
            token = crear_token(usuario.id, rol_nombre, None)

            # Preparar respuesta de usuario (cliente)
            user_data = {
                "id": str(usuario.id),
                "nombre": usuario.nombre,
                "correo": usuario.correo,
                "telefono": telefono_formateado,
                "creado_el": usuario.creado_el.isoformat()
                if usuario.creado_el
                else None,
            }

            # Solo incluir rol si existe (para usuarios legacy)
            if rol_nombre:
                user_data["rol"] = rol_nombre

            return (
                jsonify(
                    {
                        "success": True,
                        "token": token,
                        "user": user_data,
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

        # Los usuarios normales (clientes) tienen id_rol=None y id_local=None
        # Solo los empleados tienen id_rol y id_local asignados

        # Crear nuevo usuario (persona/cliente sin id_local ni id_rol)
        nuevo_usuario = Usuario(
            nombre=nombre,
            correo=correo,
            contrasena=hashed_password.decode("utf-8"),
            telefono=int(telefono_limpio),
            id_rol=None,  # Los clientes no tienen rol asignado
            id_local=None,  # Los clientes no pertenecen a un local
            terminos_aceptados=True,
            fecha_aceptacion_terminos=datetime.now(),
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
def logout(user_id=None, user_rol=None, id_local=None):
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


@auth_bp.route("/validar-rut/<rut>", methods=["GET"])
def validar_rut(rut: str):
    """
    Valida un RUT de empresa y retorna su informacion del SII.

    GET /api/auth/validar-rut/76.883.241-2

    Response 200:
        {
            "valido": true,
            "existe": true,
            "razon_social": "EMPRESA XYZ SPA",
            "glosa_giro": "RESTAURANTES, BARES Y CANTINAS"
        }

    Response 400:
        {"error": "Formato de RUT invalido"}
        {"error": "Digito verificador incorrecto"}

    Response 404:
        {"error": "RUT no encontrado en el SII"}
    """
    try:
        # Validar formato
        if not validar_formato_rut(rut):
            return jsonify(
                {"error": "Formato de RUT invalido. Use formato XX.XXX.XXX-X"}
            ), 400

        # Validar digito verificador
        if not validar_digito_verificador(rut):
            return jsonify({"error": "Digito verificador incorrecto"}), 400

        # Normalizar RUT (quitar solo puntos, mantener guión)
        # En BD se almacena como: 12345678-9
        rut_limpio = rut.replace(".", "")

        # PRIMERO: Verificar si ya existe en nuestra BD
        db = next(get_db())
        local_existente = db.execute(
            select(Local).where(Local.rut_empresa == rut_limpio)
        ).scalar_one_or_none()

        if local_existente:
            return jsonify(
                {"error": "Este RUT ya esta registrado en la plataforma"}
            ), 400

        # SEGUNDO: Consultar API SRE.cl (mas rapida que SimpleAPI)
        resultado = consultar_rut_sre(rut)

        if not resultado["valido"]:
            return jsonify({"error": resultado["error"]}), 400

        if not resultado["existe"]:
            return jsonify({"error": "RUT no encontrado en el SII"}), 404

        return jsonify(
            {
                "valido": True,
                "existe": True,
                "razon_social": resultado["razon_social"],
                "glosa_giro": resultado["glosa_giro"],
            }
        ), 200

    except Exception as e:
        logger.error(f"Error en validar_rut: {e!s}")
        return jsonify({"error": "Error al validar el RUT"}), 500


@auth_bp.route("/register-empresa", methods=["POST"])
@validate_json(RegisterEmpresaSchema)
def register_empresa(data: RegisterEmpresaSchema):
    """
    Registra una nueva empresa con su usuario gerente.
    Crea atomicamente: Direccion + Local + Usuario (gerente).

    POST /api/auth/register-empresa

    Body:
        {
            "rut_empresa": "76.883.241-2",
            "razon_social": "EMPRESA XYZ SPA",
            "nombre_local": "Restaurante XYZ",
            "telefono_local": "912345678",
            "correo_local": "contacto@xyz.cl",
            "descripcion": "Descripcion del local",
            "id_tipo_local": 1,
            "calle": "Av. Principal",
            "numero": 123,
            "id_comuna": 1,
            "nombre_gerente": "Juan Perez",
            "correo_gerente": "gerente@xyz.cl",
            "telefono_gerente": "987654321",
            "contrasena": "password123",
            "acepta_terminos": true
        }

    Response 201:
        {
            "success": true,
            "message": "Empresa registrada exitosamente",
            "local_id": 1
        }

    Response 400:
        {"error": "RUT ya registrado"}
        {"error": "Correo de local ya registrado"}
        {"error": "Correo de gerente ya registrado"}
    """
    db = None
    try:
        db = next(get_db())

        # 1. Verificar que el RUT no este registrado
        local_existente = db.execute(
            select(Local).where(Local.rut_empresa == data.rut_empresa)
        ).scalar_one_or_none()

        if local_existente:
            return jsonify({"error": "Este RUT ya esta registrado"}), 400

        # 2. Verificar correo del local
        correo_local_existente = db.execute(
            select(Local).where(Local.correo == data.correo_local.lower())
        ).scalar_one_or_none()

        if correo_local_existente:
            return jsonify({"error": "El correo del local ya esta registrado"}), 400

        # 3. Manejar gerente: vincular existente o validar nuevo
        usuario_gerente = None

        if data.id_persona:
            # Caso A: Vincular usuario existente
            usuario_gerente = db.execute(
                select(Usuario).where(Usuario.id == data.id_persona)
            ).scalar_one_or_none()

            if not usuario_gerente:
                return jsonify({"error": "Usuario no encontrado"}), 404

            # Verificar que el usuario no sea empleado de otro local
            if usuario_gerente.id_local is not None:
                return jsonify(
                    {"error": "Este usuario ya es gerente/empleado de otro local"}
                ), 400

            # Verificar que el correo coincida
            if usuario_gerente.correo != data.correo_gerente.lower():
                return jsonify(
                    {"error": "El correo del gerente no coincide con el usuario"}
                ), 400

        else:
            # Caso B: Crear nuevo usuario - validar que el correo no exista
            if not data.contrasena:
                return jsonify(
                    {"error": "Se requiere contraseña para crear nuevo usuario"}
                ), 400

            correo_gerente_existente = db.execute(
                select(Usuario).where(Usuario.correo == data.correo_gerente.lower())
            ).scalar_one_or_none()

            if correo_gerente_existente:
                return jsonify(
                    {"error": "El correo del gerente ya esta registrado"}
                ), 400

        # 4. Crear Direccion (RUT ya fue validado en paso 1 del formulario)
        nueva_direccion = Direccion(
            id_comuna=data.id_comuna,
            calle=data.calle,
            numero=data.numero,
            longitud=data.longitud,
            latitud=data.latitud,
        )
        db.add(nueva_direccion)
        db.flush()  # Obtener ID sin commit

        # 5. Crear Local
        nuevo_local = Local(
            id_direccion=nueva_direccion.id,
            id_tipo_local=data.id_tipo_local,
            nombre=data.nombre_local,
            descripcion=data.descripcion,
            telefono=int(data.telefono_local),
            correo=data.correo_local.lower(),
            rut_empresa=data.rut_empresa,
            razon_social=data.razon_social,
            glosa_giro=data.glosa_giro,  # Ya viene validado del paso 1
            terminos_aceptados=True,
            fecha_aceptacion_terminos=datetime.now(),
            version_terminos="v1.0",
        )
        db.add(nuevo_local)
        db.flush()  # Obtener ID sin commit

        # 6. Obtener rol "gerente"
        rol_gerente = db.execute(
            select(Rol).where(Rol.nombre == "gerente")
        ).scalar_one_or_none()

        rol_id = 2 if not rol_gerente else rol_gerente.id

        # 8. Crear o vincular usuario gerente
        if data.id_persona and usuario_gerente:
            # Vincular usuario existente como gerente
            usuario_gerente.id_rol = rol_id
            usuario_gerente.id_local = nuevo_local.id
            logger.info(
                f"Usuario existente {usuario_gerente.id} vinculado como gerente del local {nuevo_local.id}"
            )
        else:
            # Crear nuevo usuario gerente con contraseña
            assert data.contrasena is not None, "Se requiere contraseña"
            hashed_password = bcrypt.hashpw(
                data.contrasena.encode("utf-8"), bcrypt.gensalt()
            )

            nuevo_usuario = Usuario(
                id_rol=rol_id,
                id_local=nuevo_local.id,
                nombre=data.nombre_gerente,
                correo=data.correo_gerente.lower(),
                contrasena=hashed_password.decode("utf-8"),
                telefono=int(data.telefono_gerente),
                terminos_aceptados=True,
                fecha_aceptacion_terminos=datetime.now(),
            )
            db.add(nuevo_usuario)
            logger.info(f"Nuevo usuario gerente creado para local {nuevo_local.id}")

        # 9. Commit atomico
        db.commit()

        logger.info(
            f"Empresa registrada: {data.razon_social} (Local ID: {nuevo_local.id})"
        )

        return jsonify(
            {
                "success": True,
                "message": "Empresa registrada exitosamente",
                "local_id": nuevo_local.id,
            }
        ), 201

    except ValidationError as e:
        return jsonify({"error": "Datos invalidos", "details": e.errors()}), 400
    except Exception as e:
        logger.error(f"Error en register_empresa: {e!s}")
        if db is not None:
            with contextlib.suppress(Exception):
                db.rollback()
        return jsonify({"error": "Error al procesar la solicitud"}), 500
