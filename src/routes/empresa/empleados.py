"""
Rutas para gestión de empleados del local
Prefix: /api/empresa/empleados/*
"""

import secrets
import string

# pyrefly: ignore [missing-import]
import bcrypt
from flask import Blueprint, jsonify, request
from pydantic import BaseModel, EmailStr, ValidationError
from sqlalchemy import select

from database import get_session
from models.models import Local, Usuario
from routes.empresa import requerir_empleado, requerir_roles_empresa
from utils.jwt_helper import requerir_auth

empleados_bp = Blueprint("empleados", __name__, url_prefix="/empleados")


# ============================================
# SCHEMAS
# ============================================


class EmpleadoCreateSchema(BaseModel):
    nombre: str
    correo: EmailStr
    telefono: str | None = None
    rol: str


class EmpleadoUpdateSchema(BaseModel):
    nombre: str | None = None
    telefono: str | None = None
    rol: str | None = None


class EmpleadoEstadoSchema(BaseModel):
    estado: str


# ============================================
# HELPERS
# ============================================


def generar_contrasena(length: int = 12) -> str:
    """Genera una contraseña segura aleatoria"""
    caracteres = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(caracteres) for _ in range(length))


def hash_contrasena(contrasena: str) -> str:
    """Hash de contraseña con bcrypt"""
    return bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ============================================
# ENDPOINTS
# ============================================


@empleados_bp.route("/", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def listar_empleados(user_id, user_rol, id_local):
    """Listar todos los empleados del local"""
    db = get_session()
    try:
        stmt = select(Usuario).where(Usuario.id_local == id_local)
        empleados = db.execute(stmt).scalars().all()

        result = []
        for emp in empleados:
            result.append(
                {
                    "id": emp.id,
                    "nombre": emp.nombre,
                    "correo": emp.correo,
                    "telefono": emp.telefono,
                    "rol": emp.rol.nombre if emp.rol else None,
                    "estado": "activo",
                    "creado_el": emp.creado_el.isoformat() if emp.creado_el else None,
                }
            )

        return jsonify(result), 200
    finally:
        db.close()


@empleados_bp.route("/", methods=["POST"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def crear_empleado(user_id, user_rol, id_local):
    """Crear un nuevo empleado con contraseña auto-generada"""
    try:
        data = EmpleadoCreateSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "details": e.errors()}), 400

    roles_permitidos = ["mesero", "cocinero", "bartender", "gerente"]
    if data.rol not in roles_permitidos:
        return jsonify(
            {"error": f"Rol inválido. Permitidos: {', '.join(roles_permitidos)}"}
        ), 400

    db = get_session()
    try:
        # Verificar correo único
        stmt = select(Usuario).where(Usuario.correo == data.correo)
        existing = db.execute(stmt).scalar_one_or_none()

        if existing:
            return jsonify({"error": "Este correo ya está registrado"}), 400

        # Verificar local
        local = db.get(Local, id_local)
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Generar contraseña
        contrasena_temporal = generar_contrasena()
        contrasena_hash = hash_contrasena(contrasena_temporal)

        # Crear empleado
        nuevo_empleado = Usuario(
            id_local=id_local,
            nombre=data.nombre,
            correo=data.correo,
            telefono=data.telefono,
            contrasena=contrasena_hash,
            rol=data.rol,
        )
        db.add(nuevo_empleado)
        db.commit()
        db.refresh(nuevo_empleado)

        return jsonify(
            {
                "message": "Empleado creado exitosamente",
                "empleado": {
                    "id": nuevo_empleado.id,
                    "nombre": nuevo_empleado.nombre,
                    "correo": nuevo_empleado.correo,
                    "rol": nuevo_empleado.rol,
                },
                "_dev_contrasena_temporal": contrasena_temporal,
                "_dev_mensaje": f"En producción, se enviaría email a {data.correo} con la contraseña",
            }
        ), 201
    finally:
        db.close()


@empleados_bp.route("/<int:empleado_id>", methods=["PUT"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def actualizar_empleado(empleado_id, user_id, user_rol, id_local):
    """Actualizar datos de un empleado"""
    try:
        data = EmpleadoUpdateSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "details": e.errors()}), 400

    db = get_session()
    try:
        stmt = select(Usuario).where(
            Usuario.id == empleado_id, Usuario.id_local == id_local
        )
        empleado = db.execute(stmt).scalar_one_or_none()

        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404

        if data.nombre is not None:
            empleado.nombre = data.nombre

        if data.telefono is not None:
            empleado.telefono = data.telefono

        if data.rol is not None:
            roles_permitidos = ["mesero", "cocinero", "bartender", "gerente"]
            if data.rol not in roles_permitidos:
                return jsonify(
                    {
                        "error": f"Rol inválido. Permitidos: {', '.join(roles_permitidos)}"
                    }
                ), 400
            empleado.rol = data.rol

        db.commit()

        return jsonify(
            {
                "message": "Empleado actualizado",
                "empleado": {
                    "id": empleado.id,
                    "nombre": empleado.nombre,
                    "correo": empleado.correo,
                    "telefono": empleado.telefono,
                    "rol": empleado.rol,
                },
            }
        ), 200
    finally:
        db.close()


@empleados_bp.route("/<int:empleado_id>/estado", methods=["PATCH"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def cambiar_estado_empleado(empleado_id, user_id, user_rol, id_local):
    """Endpoint legacy - los empleados no tienen estado, se eliminan"""
    return jsonify(
        {
            "message": "Los empleados no tienen estado. Use DELETE para eliminar.",
        }
    ), 400


@empleados_bp.route("/<int:empleado_id>", methods=["DELETE"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def eliminar_empleado(empleado_id, user_id, user_rol, id_local):
    """Eliminar un empleado"""
    db = get_session()
    try:
        stmt = select(Usuario).where(
            Usuario.id == empleado_id, Usuario.id_local == id_local
        )
        empleado = db.execute(stmt).scalar_one_or_none()

        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404

        if empleado.id == user_id:
            return jsonify({"error": "No puedes eliminarte a ti mismo"}), 400

        db.delete(empleado)
        db.commit()

        return jsonify({"message": "Empleado eliminado exitosamente"}), 200
    finally:
        db.close()
