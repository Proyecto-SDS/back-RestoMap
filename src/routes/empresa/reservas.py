"""
Rutas para gestión de reservas del local
Prefix: /api/empresa/reservas/*
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_session
from models.models import EstadoReservaEnum, Reserva, ReservaMesa
from routes.empresa import requerir_empleado, requerir_roles_empresa
from utils.jwt_helper import requerir_auth

reservas_bp = Blueprint("reservas_empresa", __name__, url_prefix="/reservas")


# ============================================
# ENDPOINTS
# ============================================


@reservas_bp.route("/", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def listar_reservas(user_id, user_rol, id_local):
    """Listar todas las reservas del local"""
    fecha_filter = request.args.get("fecha")
    estado_filter = request.args.get("estado")

    db = get_session()
    try:
        stmt = (
            select(Reserva)
            .options(
                joinedload(Reserva.usuario),
                joinedload(Reserva.reservas_mesa).joinedload(ReservaMesa.mesa),
                joinedload(Reserva.qr_dinamicos),
            )
            .where(Reserva.id_local == id_local)
            .order_by(Reserva.fecha_reserva.desc(), Reserva.hora_reserva.desc())
        )

        if fecha_filter:
            from datetime import datetime

            try:
                fecha = datetime.strptime(fecha_filter, "%Y-%m-%d").date()
                stmt = stmt.where(Reserva.fecha_reserva == fecha)
            except ValueError:
                pass

        if estado_filter:
            try:
                estado_enum = EstadoReservaEnum(estado_filter)
                stmt = stmt.where(Reserva.estado == estado_enum)
            except ValueError:
                pass

        reservas = db.execute(stmt).unique().scalars().all()

        result = []
        for reserva in reservas:
            # Obtener mesas asignadas
            mesas = [rm.mesa.nombre for rm in reserva.reservas_mesa if rm.mesa]

            # Obtener codigo QR activo
            qr_codigo = None
            if reserva.qr_dinamicos:
                qr = next((q for q in reserva.qr_dinamicos if q.activo), None)
                if qr:
                    qr_codigo = qr.codigo

            result.append(
                {
                    "id": reserva.id,
                    "usuario_nombre": reserva.usuario.nombre
                    if reserva.usuario
                    else "Usuario",
                    "usuario_telefono": reserva.usuario.telefono
                    if reserva.usuario
                    else None,
                    "fecha": reserva.fecha_reserva.strftime("%Y-%m-%d")
                    if reserva.fecha_reserva
                    else None,
                    "hora": reserva.hora_reserva.strftime("%H:%M")
                    if reserva.hora_reserva
                    else None,
                    "estado": reserva.estado.value if reserva.estado else "pendiente",
                    "mesas": mesas,
                    "codigo_qr": qr_codigo or f"RES-{reserva.id}",
                    "creado_el": reserva.creado_el.isoformat()
                    if reserva.creado_el
                    else None,
                }
            )

        return jsonify(result), 200
    finally:
        db.close()


@reservas_bp.route("/<int:reserva_id>/cancelar", methods=["PATCH"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def cancelar_reserva(reserva_id, user_id, user_rol, id_local):
    """Cancelar una reserva"""
    db = get_session()
    try:
        stmt = select(Reserva).where(
            Reserva.id == reserva_id, Reserva.id_local == id_local
        )
        reserva = db.execute(stmt).scalar_one_or_none()

        if not reserva:
            return jsonify({"error": "Reserva no encontrada"}), 404

        if reserva.estado == EstadoReservaEnum.RECHAZADA:
            return jsonify({"error": "La reserva ya fue cancelada"}), 400

        reserva.estado = EstadoReservaEnum.RECHAZADA
        db.commit()

        return jsonify(
            {
                "message": "Reserva cancelada exitosamente",
                "reserva": {
                    "id": reserva.id,
                    "estado": reserva.estado.value,
                },
            }
        ), 200
    finally:
        db.close()
