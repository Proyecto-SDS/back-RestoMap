"""
Rutas para gestión de empleados e invitaciones del local
Prefix: /api/empresa/empleados/*
"""

import secrets

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, EmailStr, ValidationError
from sqlalchemy import select

from config import get_logger
from database import get_session
from models.models import EstadoInvitacionEnum, InvitacionEmpleado, Local, Rol, Usuario
from routes.empresa import requerir_empleado, requerir_roles_empresa
from utils.jwt_helper import requerir_auth

logger = get_logger(__name__)

empleados_bp = Blueprint("empleados", __name__, url_prefix="/empleados")


# ============================================
# SCHEMAS
# ============================================


class InvitacionCreateSchema(BaseModel):
    """Schema para crear una invitación de empleado"""

    correo: EmailStr
    rol: str  # mesero, cocinero, bartender, gerente


class EmpleadoUpdateSchema(BaseModel):
    nombre: str | None = None
    telefono: str | None = None
    rol: str | None = None


# ============================================
# HELPERS
# ============================================


def generar_token_invitacion() -> str:
    """Genera un token único para la invitación"""
    return secrets.token_urlsafe(32)


# ============================================
# ENDPOINTS - EMPLEADOS
# ============================================


@empleados_bp.route("/", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def listar_empleados(user_id, user_rol, id_local):
    """Listar todos los empleados activos del local"""
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
    """
    DEPRECADO: Usar /invitaciones/ para invitar empleados

    Este endpoint se mantiene por compatibilidad pero redirige a crear invitación
    """
    return crear_invitacion(user_id, user_rol, id_local)


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
                        "error": (
                            f"Rol inválido. Permitidos: {', '.join(roles_permitidos)}"
                        )
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
    """
    Despedir un empleado (remover del local).

    No elimina al usuario de la base de datos, solo le quita el rol y el local
    para que pueda seguir usando su cuenta como cliente.
    """
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

        # En lugar de eliminar, removemos el rol y local del empleado
        empleado.id_rol = None
        empleado.id_local = None
        db.commit()

        return jsonify({"message": "Empleado removido del local exitosamente"}), 200
    finally:
        db.close()


# ============================================
# ENDPOINTS - INVITACIONES
# ============================================


@empleados_bp.route("/invitaciones", methods=["POST"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def crear_invitacion(user_id, user_rol, id_local):
    """
    Crear invitación para nuevo empleado o asignar directamente si el usuario existe.

    Si el usuario ya está registrado y no tiene local, se le asigna automáticamente.
    Si el usuario ya tiene un local asignado, se retorna un error.
    Si el usuario no existe, se crea una invitación pendiente.

    Body:
        {
            "correo": "empleado@example.com",
            "rol": "mesero"  // mesero, cocinero, bartender, gerente
        }
    """
    try:
        data = InvitacionCreateSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "details": e.errors()}), 400

    roles_permitidos = ["mesero", "cocinero", "bartender", "gerente"]
    if data.rol not in roles_permitidos:
        return jsonify(
            {"error": f"Rol inválido. Permitidos: {', '.join(roles_permitidos)}"}
        ), 400

    db = get_session()
    try:
        # Verificar que el local existe
        local = db.get(Local, id_local)
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Obtener el ID del rol
        stmt = select(Rol).where(Rol.nombre == data.rol)
        rol_obj = db.execute(stmt).scalar_one_or_none()
        if not rol_obj:
            return jsonify({"error": "Rol no encontrado en el sistema"}), 404

        # Buscar si el usuario existe en el sistema
        stmt = select(Usuario).where(Usuario.correo == data.correo.lower())
        usuario_existente = db.execute(stmt).scalar_one_or_none()

        if usuario_existente:
            # El usuario existe, verificar si ya tiene un local asignado
            if usuario_existente.id_local is not None:
                if usuario_existente.id_local == id_local:
                    return jsonify(
                        {"error": "Este usuario ya es empleado de este local"}
                    ), 400
                else:
                    return jsonify(
                        {
                            "error": "Este usuario ya está registrado como empleado en otro local. "
                            "Debe ser removido del otro local antes de poder unirse a este."
                        }
                    ), 400

            # El usuario existe pero no tiene local - asignar directamente
            usuario_existente.id_local = id_local
            usuario_existente.id_rol = rol_obj.id
            db.commit()

            logger.info(
                f"Usuario {usuario_existente.correo} asignado automáticamente al local {local.nombre} como {data.rol}"
            )

            return jsonify(
                {
                    "success": True,
                    "message": f"Empleado agregado exitosamente. {usuario_existente.nombre} ahora es {data.rol} en {local.nombre}.",
                    "auto_aceptado": True,
                    "empleado": {
                        "id": usuario_existente.id,
                        "nombre": usuario_existente.nombre,
                        "correo": usuario_existente.correo,
                        "rol": data.rol,
                        "local": local.nombre,
                    },
                }
            ), 201

        # El usuario no existe en el sistema - retornar error
        return jsonify(
            {
                "error": "Este correo no está registrado en RestoMap. El usuario debe crear una cuenta primero."
            }
        ), 400
    except Exception as e:
        logger.error(f"Error al crear invitación: {e}")
        db.rollback()
        return jsonify({"error": "Error al crear la invitación"}), 500
    finally:
        db.close()


@empleados_bp.route("/invitaciones", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def listar_invitaciones(user_id, user_rol, id_local):
    """Listar invitaciones del local (pendientes, aceptadas, rechazadas)"""
    db = get_session()
    try:
        stmt = (
            select(InvitacionEmpleado)
            .where(InvitacionEmpleado.id_local == id_local)
            .order_by(InvitacionEmpleado.creado_el.desc())
        )

        invitaciones = db.execute(stmt).scalars().all()

        result = []
        for inv in invitaciones:
            result.append(
                {
                    "id": inv.id,
                    "correo": inv.correo,
                    "rol": inv.rol.nombre if inv.rol else None,
                    "estado": inv.estado.value,
                    "creado_el": inv.creado_el.isoformat() if inv.creado_el else None,
                    "expira_el": inv.expira_el.isoformat() if inv.expira_el else None,
                    "invitado_por": inv.invitador.nombre if inv.invitador else None,
                }
            )

        return jsonify(result), 200
    finally:
        db.close()


@empleados_bp.route("/invitaciones/<int:invitacion_id>", methods=["DELETE"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def cancelar_invitacion(invitacion_id, user_id, user_rol, id_local):
    """Cancelar una invitación pendiente"""
    db = get_session()
    try:
        stmt = select(InvitacionEmpleado).where(
            InvitacionEmpleado.id == invitacion_id,
            InvitacionEmpleado.id_local == id_local,
        )
        invitacion = db.execute(stmt).scalar_one_or_none()

        if not invitacion:
            return jsonify({"error": "Invitación no encontrada"}), 404

        if invitacion.estado != EstadoInvitacionEnum.PENDIENTE:
            return jsonify(
                {"error": "Solo se pueden cancelar invitaciones pendientes"}
            ), 400

        db.delete(invitacion)
        db.commit()

        return jsonify({"message": "Invitación cancelada exitosamente"}), 200
    finally:
        db.close()
