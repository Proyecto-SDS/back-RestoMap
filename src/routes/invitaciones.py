"""
Rutas públicas para gestión de invitaciones de empleados
Endpoints: /api/invitaciones/*
"""

from datetime import datetime

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ValidationError
from sqlalchemy import select

from config import get_logger
from database import get_session
from models.models import EstadoInvitacionEnum, InvitacionEmpleado, Usuario
from utils.jwt_helper import requerir_auth

logger = get_logger(__name__)

invitaciones_bp = Blueprint("invitaciones", __name__, url_prefix="/api/invitaciones")


# ============================================
# SCHEMAS
# ============================================


class AceptarInvitacionSchema(BaseModel):
    """Schema para aceptar una invitación (usuario ya registrado)"""

    token: str


# ============================================
# ENDPOINTS PÚBLICOS
# ============================================


@invitaciones_bp.route("/<token>", methods=["GET"])
def obtener_invitacion(token: str):
    """
    Obtener detalles de una invitación por token (público)

    Permite al usuario ver los detalles de la invitación antes de aceptarla
    """
    db = get_session()
    try:
        stmt = select(InvitacionEmpleado).where(InvitacionEmpleado.token == token)
        invitacion = db.execute(stmt).scalar_one_or_none()

        if not invitacion:
            return jsonify({"error": "Invitación no encontrada"}), 404

        # Verificar si ya expiró
        if invitacion.expira_el < datetime.now():
            if invitacion.estado == EstadoInvitacionEnum.PENDIENTE:
                invitacion.estado = EstadoInvitacionEnum.EXPIRADA
                db.commit()
            return jsonify({"error": "Esta invitación ha expirado"}), 410

        # Verificar estado
        if invitacion.estado != EstadoInvitacionEnum.PENDIENTE:
            return jsonify(
                {
                    "error": f"Esta invitación ya fue {invitacion.estado.value}",
                    "estado": invitacion.estado.value,
                }
            ), 400

        return jsonify(
            {
                "correo": invitacion.correo,
                "rol": invitacion.rol.nombre if invitacion.rol else None,
                "local": {
                    "id": invitacion.local.id,
                    "nombre": invitacion.local.nombre,
                },
                "invitado_por": invitacion.invitador.nombre
                if invitacion.invitador
                else None,
                "expira_el": invitacion.expira_el.isoformat(),
            }
        ), 200
    finally:
        db.close()


@invitaciones_bp.route("/aceptar", methods=["POST"])
@requerir_auth
def aceptar_invitacion(user_id, user_rol, id_local):
    """
    Aceptar invitación de empleado (requiere autenticación)

    El usuario debe estar logueado. Si el correo de la invitación coincide
    con el correo del usuario autenticado, se acepta la invitación y el
    usuario se convierte en empleado del local.

    Body:
        {
            "token": "abc123..."
        }
    """
    try:
        data = AceptarInvitacionSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "details": e.errors()}), 400

    db = get_session()
    try:
        # Buscar invitación
        stmt = select(InvitacionEmpleado).where(InvitacionEmpleado.token == data.token)
        invitacion = db.execute(stmt).scalar_one_or_none()

        if not invitacion:
            return jsonify({"error": "Invitación no encontrada"}), 404

        # Verificar expiración
        if invitacion.expira_el < datetime.now():
            if invitacion.estado == EstadoInvitacionEnum.PENDIENTE:
                invitacion.estado = EstadoInvitacionEnum.EXPIRADA
                db.commit()
            return jsonify({"error": "Esta invitación ha expirado"}), 410

        # Verificar estado
        if invitacion.estado != EstadoInvitacionEnum.PENDIENTE:
            return jsonify(
                {
                    "error": f"Esta invitación ya fue {invitacion.estado.value}",
                }
            ), 400

        # Obtener usuario autenticado
        usuario = db.get(Usuario, user_id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # Verificar que el correo coincida
        if usuario.correo.lower() != invitacion.correo.lower():
            return jsonify(
                {
                    "error": "El correo de tu cuenta no coincide con el de la invitación",
                    "correo_invitacion": invitacion.correo,
                    "correo_usuario": usuario.correo,
                }
            ), 403

        # Verificar si ya es empleado de este local
        if usuario.id_local == invitacion.id_local:
            return jsonify({"error": "Ya eres empleado de este local"}), 400

        # Verificar si ya es empleado de otro local
        if usuario.id_local is not None:
            return jsonify(
                {
                    "error": "Ya eres empleado de otro local. No puedes aceptar esta invitación."
                }
            ), 400

        # Aceptar invitación: convertir usuario en empleado
        usuario.id_local = invitacion.id_local
        usuario.id_rol = invitacion.id_rol
        usuario.invitado_por = invitacion.invitado_por

        # Actualizar estado de invitación
        invitacion.estado = EstadoInvitacionEnum.ACEPTADA
        invitacion.aceptado_el = datetime.now()

        db.commit()
        db.refresh(usuario)

        return jsonify(
            {
                "success": True,
                "message": "Invitación aceptada exitosamente",
                "empleado": {
                    "id": usuario.id,
                    "nombre": usuario.nombre,
                    "correo": usuario.correo,
                    "rol": usuario.rol.nombre if usuario.rol else None,
                    "local": {
                        "id": invitacion.local.id,
                        "nombre": invitacion.local.nombre,
                    },
                },
            }
        ), 200
    except Exception as e:
        logger.error(f"Error al aceptar invitación: {e}")
        db.rollback()
        return jsonify({"error": "Error al aceptar la invitación"}), 500
    finally:
        db.close()


@invitaciones_bp.route("/rechazar", methods=["POST"])
@requerir_auth
def rechazar_invitacion(user_id, user_rol, id_local):
    """
    Rechazar invitación de empleado (requiere autenticación)

    Body:
        {
            "token": "abc123..."
        }
    """
    try:
        data = AceptarInvitacionSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "details": e.errors()}), 400

    db = get_session()
    try:
        # Buscar invitación
        stmt = select(InvitacionEmpleado).where(InvitacionEmpleado.token == data.token)
        invitacion = db.execute(stmt).scalar_one_or_none()

        if not invitacion:
            return jsonify({"error": "Invitación no encontrada"}), 404

        # Verificar estado
        if invitacion.estado != EstadoInvitacionEnum.PENDIENTE:
            return jsonify(
                {
                    "error": f"Esta invitación ya fue {invitacion.estado.value}",
                }
            ), 400

        # Obtener usuario autenticado
        usuario = db.get(Usuario, user_id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # Verificar que el correo coincida
        if usuario.correo.lower() != invitacion.correo.lower():
            return jsonify(
                {"error": "El correo de tu cuenta no coincide con el de la invitación"}
            ), 403

        # Rechazar invitación
        invitacion.estado = EstadoInvitacionEnum.RECHAZADA
        invitacion.rechazado_el = datetime.now()

        db.commit()

        return jsonify(
            {
                "success": True,
                "message": "Invitación rechazada",
            }
        ), 200
    except Exception as e:
        logger.error(f"Error al rechazar invitación: {e}")
        db.rollback()
        return jsonify({"error": "Error al rechazar la invitación"}), 500
    finally:
        db.close()
