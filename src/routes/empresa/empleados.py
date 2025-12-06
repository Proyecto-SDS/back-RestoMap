"""
Rutas para gestión de empleados e invitaciones del local
Prefix: /api/empresa/empleados/*
"""

import secrets
from datetime import datetime, timedelta

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


# ============================================
# ENDPOINTS - INVITACIONES
# ============================================


@empleados_bp.route("/invitaciones", methods=["POST"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def crear_invitacion(user_id, user_rol, id_local):
    """
    Crear invitación para nuevo empleado

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

        # Verificar si el usuario ya es empleado del local
        stmt = select(Usuario).where(
            Usuario.correo == data.correo.lower(), Usuario.id_local == id_local
        )
        usuario_existente = db.execute(stmt).scalar_one_or_none()
        if usuario_existente:
            return jsonify({"error": "Este usuario ya es empleado de este local"}), 400

        # Verificar si ya existe una invitación pendiente
        stmt = select(InvitacionEmpleado).where(
            InvitacionEmpleado.correo == data.correo.lower(),
            InvitacionEmpleado.id_local == id_local,
            InvitacionEmpleado.estado == EstadoInvitacionEnum.PENDIENTE,
        )
        invitacion_existente = db.execute(stmt).scalar_one_or_none()
        if invitacion_existente:
            return jsonify(
                {"error": "Ya existe una invitación pendiente para este correo"}
            ), 400

        # Obtener el ID del rol
        stmt = select(Rol).where(Rol.nombre == data.rol)
        rol_obj = db.execute(stmt).scalar_one_or_none()
        if not rol_obj:
            return jsonify({"error": "Rol no encontrado en el sistema"}), 404

        # Crear invitación
        token = generar_token_invitacion()
        expiracion = datetime.now() + timedelta(days=7)  # Expira en 7 días

        nueva_invitacion = InvitacionEmpleado(
            id_local=id_local,
            id_rol=rol_obj.id,
            invitado_por=user_id,
            correo=data.correo.lower(),
            token=token,
            estado=EstadoInvitacionEnum.PENDIENTE,
            expira_el=expiracion,
        )

        db.add(nueva_invitacion)
        db.commit()
        db.refresh(nueva_invitacion)

        # TODO: Enviar email con el link de invitación
        # link_invitacion = f"{FRONTEND_URL}/invitacion/{token}"
        # enviar_email_invitacion(data.correo, local.nombre, data.rol, link_invitacion)

        return jsonify(
            {
                "success": True,
                "message": "Invitación creada exitosamente",
                "invitacion": {
                    "id": nueva_invitacion.id,
                    "correo": nueva_invitacion.correo,
                    "rol": data.rol,
                    "local": local.nombre,
                    "expira_el": nueva_invitacion.expira_el.isoformat(),
                },
                "_dev_token": token,
                "_dev_mensaje": f"En producción, se enviaría email a {data.correo}",
            }
        ), 201
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
